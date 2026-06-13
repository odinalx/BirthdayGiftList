import logging
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.debug("JWT decode failed: %s", e)
        return None


def verify_access_token(token: str) -> str | None:
    """Verify access token and return user_id if valid."""
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != "access":
        return None
    return payload.get("sub")


def verify_refresh_token(token: str) -> str | None:
    """Verify refresh token and return user_id if valid."""
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != "refresh":
        return None
    return payload.get("sub")
