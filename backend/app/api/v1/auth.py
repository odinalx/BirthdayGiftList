import logging
import secrets
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.responses import RedirectResponse
from nanoid import generate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotAuthenticatedException
from app.core.security import create_access_token, create_refresh_token, verify_refresh_token
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.auth import exchange_code_for_token, get_google_authorization_url, get_google_user_info

router = APIRouter()
logger = logging.getLogger(__name__)

IS_PRODUCTION = settings.frontend_url.startswith("https")


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")


@router.get("/google/login")
async def google_login():
    url, state = get_google_authorization_url()
    response = RedirectResponse(url=url)
    response.set_cookie("oauth_state", state, httponly=True, secure=IS_PRODUCTION, samesite="lax", max_age=600)
    return response


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
    oauth_state: str | None = Cookie(default=None),
):
    if not oauth_state or not secrets.compare_digest(state, oauth_state):
        logger.warning("OAuth state validation failed")
        return RedirectResponse(url=f"{settings.frontend_url}?error=auth_failed&message=invalid_state")

    try:
        token_data = await exchange_code_for_token(code)
        user_info = await get_google_user_info(token_data["access_token"])

        result = await db.execute(select(User).where(User.google_id == user_info["id"]))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                google_id=user_info["id"],
                email=user_info["email"],
                name=user_info.get("name", user_info["email"]),
                picture=user_info.get("picture"),
                list_slug=generate(size=10),
            )
            db.add(user)
            await db.flush()
        else:
            user.name = user_info.get("name", user.name)
            user.picture = user_info.get("picture")

        await db.commit()

        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        response = RedirectResponse(url=f"{settings.frontend_url}/oauth/callback", status_code=status.HTTP_302_FOUND)
        _set_auth_cookies(response, access_token, refresh_token)
        response.delete_cookie(key="oauth_state")
        return response

    except Exception:
        logger.exception("OAuth callback failed")
        return RedirectResponse(url=f"{settings.frontend_url}?error=auth_failed&message=authentication_error")


@router.post("/refresh")
async def refresh_token_endpoint(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token_cookie: str | None = Cookie(default=None, alias="refresh_token"),
):
    if not refresh_token_cookie:
        raise NotAuthenticatedException()

    user_id = verify_refresh_token(refresh_token_cookie)
    if user_id is None:
        _clear_auth_cookies(response)
        raise NotAuthenticatedException()

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        _clear_auth_cookies(response)
        raise NotAuthenticatedException()

    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    _set_auth_cookies(response, access_token, new_refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    _clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/session")
async def get_session(
    response: Response,
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None),
    refresh_token_cookie: str | None = Cookie(default=None, alias="refresh_token"),
):
    from app.core.security import verify_access_token

    if access_token:
        user_id = verify_access_token(access_token)
        if user_id:
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            if user:
                return {"authenticated": True, "user": UserResponse.model_validate(user)}

    if refresh_token_cookie:
        user_id = verify_refresh_token(refresh_token_cookie)
        if user_id:
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            if user:
                new_access_token = create_access_token(data={"sub": str(user.id)})
                new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
                _set_auth_cookies(response, new_access_token, new_refresh_token)
                return {"authenticated": True, "user": UserResponse.model_validate(user)}

    _clear_auth_cookies(response)
    return {"authenticated": False, "user": None}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
