import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.seat import SeatClass, SeatStatus


class SeatResponse(BaseModel):
    id: uuid.UUID
    flight_id: uuid.UUID
    seat_number: str
    seat_class: SeatClass
    status: SeatStatus

    model_config = ConfigDict(from_attributes=True)


class SeatMapResponse(BaseModel):
    flight_id: uuid.UUID
    flight_number: str
    total_seats: int
    available_seats: int
    held_seats: int
    booked_seats: int
    blocked_seats: int
    seats: List[SeatResponse]


class InventoryAdjustmentRequest(BaseModel):
    first_seats: int = Field(..., ge=0, examples=[20])
    business_seats: int = Field(..., ge=0, examples=[30])
    economy_seats: int = Field(..., ge=0, examples=[50])
