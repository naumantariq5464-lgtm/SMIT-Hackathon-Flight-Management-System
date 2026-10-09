import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.cancellation import CancellationType


class CancellationRequest(BaseModel):
    reason: str = Field(default="Passenger request", min_length=2, max_length=255)


class PartialPassengerCancellationRequest(BaseModel):
    passenger_ids: List[uuid.UUID] = Field(..., min_length=1)
    reason: str = Field(default="Partial passenger cancellation", min_length=2, max_length=255)


class CancellationResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    cancellation_type: CancellationType
    affected_passenger_ids: str
    original_amount: Decimal
    refund_amount: Decimal
    credit_amount: Decimal
    penalty_amount: Decimal
    currency: str
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
