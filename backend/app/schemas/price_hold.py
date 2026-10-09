import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models.price_hold import HoldStatus
from app.models.seat import SeatClass


class PriceHoldCreate(BaseModel):
    flight_id: uuid.UUID
    seat_class: SeatClass
    fare_rule_id: uuid.UUID
    passenger_count: int = Field(default=1, gt=0, le=9)


class PriceHoldResponse(BaseModel):
    id: uuid.UUID
    flight_id: uuid.UUID
    user_id: uuid.UUID
    seat_class: SeatClass
    fare_rule_id: uuid.UUID
    passenger_count: int
    held_price_per_passenger: Decimal
    total_held_price: Decimal
    currency: str
    status: HoldStatus
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
