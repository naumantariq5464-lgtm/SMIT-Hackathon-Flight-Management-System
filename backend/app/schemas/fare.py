import uuid
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.fare_rule import FareType
from app.models.seat import SeatClass


class FareRuleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    fare_type: FareType
    seat_class: SeatClass
    is_refundable: bool = False
    refund_penalty_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    travel_credit_eligible: bool = True
    seat_selection_allowed: bool = False
    change_allowed: bool = False
    change_fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    multiplier: Decimal = Field(default=Decimal("1.00"), gt=0)
    baggage_allowance_kg: int = Field(default=20, ge=0)


class FareRuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    fare_type: FareType
    seat_class: SeatClass
    is_refundable: bool
    refund_penalty_percent: Decimal
    travel_credit_eligible: bool
    seat_selection_allowed: bool
    change_allowed: bool
    change_fee: Decimal
    multiplier: Decimal
    baggage_allowance_kg: int

    model_config = ConfigDict(from_attributes=True)
