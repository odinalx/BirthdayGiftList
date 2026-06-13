from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.gift import GiftStatus


class GiftResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    image_url: str | None = None
    link: str | None = None
    price: float | None = None
    status: GiftStatus
    claimed_by_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GiftCreate(BaseModel):
    title: str
    description: str | None = None
    image_url: str | None = None
    link: str | None = None
    price: float | None = None


class GiftUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    link: str | None = None
    price: float | None = None
    status: GiftStatus | None = None


class ReserveRequest(BaseModel):
    visitor_name: str
    visitor_id: str


class UnreserveRequest(BaseModel):
    visitor_id: str
