from uuid import UUID

from fastapi import Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotAuthenticatedException
from app.core.security import verify_access_token
from app.database import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    access_token_cookie: str | None = Cookie(default=None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token_cookie:
        token = access_token_cookie

    if not token:
        raise NotAuthenticatedException()

    user_id = verify_access_token(token)
    if user_id is None:
        raise NotAuthenticatedException()

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise NotAuthenticatedException() from None

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotAuthenticatedException()

    return user
