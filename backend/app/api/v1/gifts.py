import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.gift import Gift, GiftStatus
from app.models.user import User
from app.schemas.gift import GiftCreate, GiftResponse, GiftUpdate, ReserveRequest, UnreserveRequest

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


# Public endpoints (no auth required)

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
