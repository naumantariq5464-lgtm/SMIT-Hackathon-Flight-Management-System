import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.seat import SeatClass
from app.models.user import LoyaltyTier
from app.models.waitlist import WaitlistStatus


class WaitlistJoinRequest(BaseModel):
    flight_id: uuid.UUID
    requested_class: SeatClass = SeatClass.ECONOMY


class WaitlistResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    flight_id: uuid.UUID
    requested_class: SeatClass
    loyalty_tier: LoyaltyTier
    priority_score: int
    status: WaitlistStatus
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
