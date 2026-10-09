import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.refund import RefundStatus


class RefundResponse(BaseModel):
    id: uuid.UUID
    cancellation_id: Optional[uuid.UUID]
    booking_id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    currency: str
    status: RefundStatus
    reason: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RefundStatusUpdateRequest(BaseModel):
    status: RefundStatus
