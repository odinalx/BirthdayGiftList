from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class GiftStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    BOUGHT = "BOUGHT"


class Gift(Base, TimestampMixin):
    __tablename__ = "gifts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped[User] = relationship(back_populates="gifts")

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    status: Mapped[GiftStatus] = mapped_column(
        Enum(GiftStatus, name="giftstatus"), default=GiftStatus.AVAILABLE
    )
    claimed_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claimed_by_visitor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
