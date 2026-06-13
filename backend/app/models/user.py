from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.gift import Gift


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    list_slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    gifts: Mapped[list[Gift]] = relationship(back_populates="user", cascade="all, delete-orphan")
