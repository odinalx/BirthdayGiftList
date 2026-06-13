import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client

from app.config import settings

GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_authorization_url() -> tuple[str, str]:
    """Generate Google OAuth authorization URL and state."""
    client = AsyncOAuth2Client(
        client_id=settings.google_client_id,
        redirect_uri=settings.google_redirect_uri,
    )
    url, state = client.create_authorization_url(
        GOOGLE_AUTHORIZATION_URL,
        scope="openid email profile",
    )
    return url, state


async def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token."""
    async with AsyncOAuth2Client(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
    ) as client:
        token = await client.fetch_token(
            GOOGLE_TOKEN_URL,
            code=code,
        )
        return token


async def get_google_user_info(access_token: str) -> dict:
    """Fetch user info from Google using access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()
