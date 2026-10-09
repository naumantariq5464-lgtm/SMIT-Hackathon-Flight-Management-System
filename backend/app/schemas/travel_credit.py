import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.travel_credit import TravelCreditStatus


class TravelCreditResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    booking_id: Optional[uuid.UUID]
    code: str
    amount: Decimal
    balance: Decimal
    currency: str
    status: TravelCreditStatus
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TravelCreditRedeemRequest(BaseModel):
    code: str = Field(..., min_length=5, max_length=30)
    amount: Decimal = Field(..., gt=0)
