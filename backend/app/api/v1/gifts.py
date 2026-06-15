import json
import logging
import re
from html import unescape
from html.parser import HTMLParser
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.gift import Gift, GiftStatus
from app.models.user import User
from app.schemas.gift import (
    BuyRequest,
    GiftCreate,
    GiftResponse,
    GiftUpdate,
    ReserveRequest,
    UnreserveRequest,
    UrlFetchRequest,
    UrlMetaResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=list[GiftResponse])
async def get_my_gifts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Gift).where(Gift.user_id == current_user.id).order_by(Gift.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=GiftResponse, status_code=201)
async def create_gift(
    data: GiftCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gift = Gift(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        image_url=data.image_url,
        link=data.link,
        price=data.price,
    )
    db.add(gift)
    await db.flush()
    await db.refresh(gift)
    return gift


@router.patch("/{gift_id}", response_model=GiftResponse)
async def update_gift(
    gift_id: UUID,
    data: GiftUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Gift).where(Gift.id == gift_id, Gift.user_id == current_user.id)
    )
    gift = result.scalar_one_or_none()
    if gift is None:
        raise HTTPException(status_code=404, detail="Gift not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(gift, field, value)

    if data.status == GiftStatus.AVAILABLE:
        gift.claimed_by_name = None
        gift.claimed_by_visitor_id = None

    await db.flush()
    await db.refresh(gift)
    return gift


@router.delete("/{gift_id}", status_code=204)
async def delete_gift(
    gift_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Gift).where(Gift.id == gift_id, Gift.user_id == current_user.id)
    )
    gift = result.scalar_one_or_none()
    if gift is None:
        raise HTTPException(status_code=404, detail="Gift not found")
    await db.delete(gift)


# ── Public endpoints (no auth required) ──────────────────────────────────────


class _OGParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.og: dict[str, str] = {}
        self.twitter: dict[str, str] = {}
        self.meta_desc: str | None = None
        self.page_title: str | None = None
        self.price_raw: str | None = None
        self.link_image: str | None = None  # <link rel="image_src">
        self._in_title = False
        self._in_script = False
        self._script_type = ""
        self._script_buf = ""

    def handle_starttag(self, tag, attrs):  # noqa: C901
        attrs_dict = dict(attrs)
        if tag == "meta":
            prop = attrs_dict.get("property", "")
            name = attrs_dict.get("name", "")
            itemprop = attrs_dict.get("itemprop", "")
            content = attrs_dict.get("content", "").strip()
            if not content:
                return
            # Open Graph
            if prop.startswith("og:"):
                key = prop[3:]
                if key in ("title", "description", "image", "image:secure_url"):
                    # prefer image:secure_url but don't overwrite og:image if set
                    store_key = "image" if "image" in key else key
                    if store_key not in self.og:
                        self.og[store_key] = content
            # Twitter Card (property or name variants)
            elif prop.startswith("twitter:") or name.startswith("twitter:"):
                raw_key = (prop or name)[8:].replace(":src", "")
                if raw_key in ("title", "description", "image"):
                    if raw_key not in self.twitter:
                        self.twitter[raw_key] = content
            # Facebook / shop product price
            elif prop in ("product:price:amount", "og:price:amount") and not self.price_raw:
                self.price_raw = content
            # Generic meta description
            elif name == "description" and not self.meta_desc:
                self.meta_desc = content
            # Schema.org microdata price on <meta>
            elif itemprop == "price" and not self.price_raw:
                self.price_raw = content
            # Schema.org microdata image on <meta>
            elif itemprop == "image" and not self.og.get("image"):
                self.og["image"] = content
        elif tag == "link":
            rel = attrs_dict.get("rel", "")
            href = attrs_dict.get("href", "").strip()
            if rel == "image_src" and href and not self.link_image:
                self.link_image = href
        elif tag == "title":
            self._in_title = True
        elif tag == "script":
            self._in_script = True
            self._script_type = attrs_dict.get("type", "")
            self._script_buf = ""

    def handle_data(self, data):
        if self._in_title and not self.page_title:
            self.page_title = data.strip()
        elif self._in_script:
            self._script_buf += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_script = False
            if self._script_type == "application/ld+json" and self._script_buf.strip():
                self._parse_jsonld(self._script_buf)

    def _parse_jsonld(self, text: str) -> None:
        try:
            data = json.loads(text)
        except Exception:
            return
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                self._extract_product(item)

    def _extract_product(self, item: dict) -> None:
        if "@graph" in item:
            for sub in item["@graph"]:
                if isinstance(sub, dict):
                    self._extract_product(sub)
            return
        t = item.get("@type", "")
        types = t if isinstance(t, list) else [t]
        if not any(x in ("Product", "IndividualProduct") for x in types):
            return
        # Image from JSON-LD (often not in og:image for shops)
        if not self.og.get("image"):
            img = item.get("image")
            if isinstance(img, list) and img:
                img = img[0]
            if isinstance(img, str) and img:
                self.og["image"] = img
            elif isinstance(img, dict) and img.get("url"):
                self.og["image"] = img["url"]
        # Description from JSON-LD
        desc = item.get("description", "")
        if desc and not self.og.get("description"):
            self.og["description"] = str(desc)[:500]
        # Price from offers
        if self.price_raw:
            return
        offers = item.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if isinstance(offers, dict):
            price = offers.get("price") or offers.get("lowPrice")
            if price is not None:
                self.price_raw = str(price)


def _parse_price(raw: str | None) -> float | None:
    if not raw:
        return None
    cleaned = re.sub(r"[^\d,.]", "", raw.strip())
    if not cleaned:
        return None
    # "249,99" → decimal comma
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    # "1.249,99" → thousand dot + decimal comma
    elif "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


_BOT_CHALLENGE_MARKERS = (
    "challenges.cloudflare.com",
    "_cf_chl_",
    "__cf_chl_jschl",
    "cf-browser-verification",
    "DDoS protection by Cloudflare",
    "Enable JavaScript and cookies to continue",
    "verifying you are human",
)

_BOT_PAGE_TITLES = frozenset(
    t.casefold()
    for t in (
        "Just a moment...",
        "Just a moment",
        "Access Denied",
        "403 Forbidden",
        "Robot or human?",
        "Attention Required! | Cloudflare",
        "Please Wait... | Cloudflare",
        "Security Check",
        "One moment, please...",
        "Bot or Not?",
        "Robot Check",
    )
)

_AMAZON_DOMAIN_RE = re.compile(
    r"amazon\.(com|fr|co\.uk|de|es|it|ca|co\.jp|com\.mx|com\.br|com\.au|nl|se|pl|sg|ae|in)",
    re.IGNORECASE,
)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "cache-control": "max-age=0",
}


def _is_bot_challenge(status: int, html: str) -> bool:
    if status not in (200, 301, 302, 303, 307, 308):
        return True
    snippet = html[:8_000]
    return any(m in snippet for m in _BOT_CHALLENGE_MARKERS)


def _parse_amazon(html: str) -> dict:
    """Extract product data from Amazon product page HTML."""
    result: dict = {}

    # Title
    m = re.search(r'id="productTitle"[^>]*>\s*(.*?)\s*</span>', html, re.DOTALL | re.IGNORECASE)
    if m:
        raw = re.sub(r"<[^>]+>", "", m.group(1))
        result["title"] = re.sub(r"\s+", " ", unescape(raw)).strip()

    # data-old-hires is the reliable high-res source Amazon embeds server-side
    m = re.search(r'data-old-hires="(https://[^"]+)"', html)
    if m:
        result["image_url"] = unescape(m.group(1))

    # Fallback: data-a-dynamic-image (JSON map, sometimes empty on SSR)
    if "image_url" not in result:
        m = re.search(r'data-a-dynamic-image="([^"]+)"', html)
        if m:
            try:
                imgs = json.loads(unescape(m.group(1)))
                if imgs:
                    result["image_url"] = next(iter(imgs))
            except Exception:
                pass

    # Feature bullets as description (first 3 non-trivial bullets)
    bullets_m = re.search(r'id="feature-bullets".*?</ul>', html, re.DOTALL)
    if bullets_m:
        items = re.findall(
            r'<span class="a-list-item">\s*(.*?)\s*</span>',
            bullets_m.group(0),
            re.DOTALL,
        )
        clean = []
        for b in items[:4]:
            b = unescape(re.sub(r"<[^>]+>", "", b)).strip()
            if b and len(b) > 10:
                clean.append(b)
        if clean:
            result["description"] = " · ".join(clean[:3])[:500]

    # Price — whole + optional fraction
    pm = re.search(r'class="a-price-whole">([^<]+)<', html)
    if pm:
        price_str = pm.group(1).strip().rstrip(".")
        fm = re.search(r'class="a-price-fraction">([^<]+)<', html)
        if fm:
            price_str += "." + fm.group(1).strip()
        result["price_raw"] = price_str

    return result


@router.post("/fetch-meta", response_model=UrlMetaResponse)
async def fetch_url_meta(data: UrlFetchRequest):
    is_amazon = bool(_AMAZON_DOMAIN_RE.search(data.url))

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(data.url, headers=_BROWSER_HEADERS)
            html = resp.text[:500_000]
    except Exception:
        return UrlMetaResponse()

    if _is_bot_challenge(resp.status_code, html):
        return UrlMetaResponse()

    parser = _OGParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    title = parser.og.get("title") or parser.twitter.get("title") or parser.page_title
    description = (
        parser.og.get("description")
        or parser.twitter.get("description")
        or parser.meta_desc
    )
    image_url = (
        parser.og.get("image")
        or parser.twitter.get("image")
        or parser.link_image
    )
    price_raw = parser.price_raw

    # Amazon-specific extraction fills gaps left by OG parser
    if is_amazon:
        amz = _parse_amazon(html)
        if not title and amz.get("title"):
            title = amz["title"]
        if not description and amz.get("description"):
            description = amz["description"]
        if not image_url and amz.get("image_url"):
            image_url = amz["image_url"]
        if not price_raw and amz.get("price_raw"):
            price_raw = amz["price_raw"]

    # Filter bot-challenge titles that slipped through (non-403 challenges)
    if title and title.casefold() in _BOT_PAGE_TITLES:
        return UrlMetaResponse()

    # Drop description when it is identical to title
    if description and title and description.strip() == title.strip():
        description = None

    return UrlMetaResponse(
        title=title,
        description=description,
        image_url=image_url,
        price=_parse_price(price_raw),
    )


from fastapi.responses import Response as FastAPIResponse  # noqa: E402


@router.get("/proxy-image")
async def proxy_image(url: str):
    """Proxy an image URL through our server so the browser can display it
    without CORS / hotlink issues."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=8) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
                    "Referer": url.split("/")[0] + "//" + url.split("/")[2] + "/",
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                },
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=404)
        content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=415)
        return FastAPIResponse(
            content=resp.content,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502)


@router.get("/public/{slug}", response_model=list[GiftResponse])
async def get_public_gifts(slug: str, db: AsyncSession = Depends(get_db)):
    from app.models.user import User as UserModel

    result = await db.execute(select(UserModel).where(UserModel.list_slug == slug))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="List not found")

    result = await db.execute(
        select(Gift).where(Gift.user_id == user.id).order_by(Gift.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{gift_id}/reserve", response_model=GiftResponse)
async def reserve_gift(
    gift_id: UUID,
    data: ReserveRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Gift).where(Gift.id == gift_id))
    gift = result.scalar_one_or_none()
    if gift is None:
        raise HTTPException(status_code=404, detail="Gift not found")
    if gift.status != GiftStatus.AVAILABLE:
        raise HTTPException(status_code=409, detail="Gift is no longer available")

    gift.status = GiftStatus.RESERVED
    gift.claimed_by_name = data.visitor_name
    gift.claimed_by_visitor_id = data.visitor_id

    await db.flush()
    await db.refresh(gift)
    return gift


@router.post("/{gift_id}/unreserve", response_model=GiftResponse)
async def unreserve_gift(
    gift_id: UUID,
    data: UnreserveRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Gift).where(Gift.id == gift_id))
    gift = result.scalar_one_or_none()
    if gift is None:
        raise HTTPException(status_code=404, detail="Gift not found")
    if gift.status != GiftStatus.RESERVED:
        raise HTTPException(status_code=409, detail="Gift is not reserved")
    if gift.claimed_by_visitor_id != data.visitor_id:
        raise HTTPException(status_code=403, detail="You did not reserve this gift")

    gift.status = GiftStatus.AVAILABLE
    gift.claimed_by_name = None
    gift.claimed_by_visitor_id = None

    await db.flush()
    await db.refresh(gift)
    return gift


@router.post("/{gift_id}/buy", response_model=GiftResponse)
async def buy_gift(
    gift_id: UUID,
    data: BuyRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Gift).where(Gift.id == gift_id))
    gift = result.scalar_one_or_none()
    if gift is None:
        raise HTTPException(status_code=404, detail="Gift not found")
    if gift.status != GiftStatus.RESERVED:
        raise HTTPException(status_code=409, detail="Gift is not reserved")
    if gift.claimed_by_visitor_id != data.visitor_id:
        raise HTTPException(status_code=403, detail="You did not reserve this gift")

    gift.status = GiftStatus.BOUGHT

    await db.flush()
    await db.refresh(gift)
    return gift
