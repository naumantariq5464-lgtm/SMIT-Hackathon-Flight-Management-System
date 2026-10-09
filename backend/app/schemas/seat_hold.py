import uuid
from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, Field
from app.models.price_hold import HoldStatus


class SeatHoldCreate(BaseModel):
    flight_id: uuid.UUID
    seat_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=9)


class SingleSeatHoldItem(BaseModel):
    hold_id: uuid.UUID
    seat_id: uuid.UUID
    seat_number: str
    status: HoldStatus
    expires_at: datetime


class SeatHoldResponse(BaseModel):
    flight_id: uuid.UUID
    user_id: uuid.UUID
    expires_at: datetime
    held_seats: List[SingleSeatHoldItem]
