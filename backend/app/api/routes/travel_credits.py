from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.travel_credit import TravelCreditResponse
from app.services.travel_credit_service import TravelCreditService

router = APIRouter(prefix="/travel-credits", tags=["Travel Credits"])


@router.get(
    "/me",
    response_model=List[TravelCreditResponse],
    summary="List all travel credits issued to current user",
)
async def get_my_travel_credits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TravelCreditResponse]:
    credits = await TravelCreditService.list_user_credits(db, current_user.id)
    return [TravelCreditResponse.model_validate(c) for c in credits]
