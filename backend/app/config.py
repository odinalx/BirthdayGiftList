from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: Literal["dev", "prod"] = "dev"

    @property
    def debug(self) -> bool:
        return self.environment == "dev"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/birthday_gift"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    jwt_secret_key: str = "change-me-in-production-make-it-long-enough"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    frontend_url: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment != "prod":
            return self
        errors = []
        if self.jwt_secret_key == "change-me-in-production-make-it-long-enough":
            errors.append("JWT_SECRET_KEY must be changed from default in production")
        if not self.google_client_id:
            errors.append("GOOGLE_CLIENT_ID is required in production")
        if not self.google_client_secret:
            errors.append("GOOGLE_CLIENT_SECRET is required in production")
        if not self.frontend_url.startswith("https://"):
            errors.append("FRONTEND_URL must use HTTPS in production")
        if errors:
            raise ValueError(f"Production configuration errors: {'; '.join(errors)}")
        return self


settings = Settings()
