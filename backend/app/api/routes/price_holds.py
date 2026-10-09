from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.price_hold import PriceHoldCreate, PriceHoldResponse
from app.services.price_hold_service import PriceHoldService

router = APIRouter(prefix="/price-holds", tags=["Price Holds"])


@router.post(
    "",
    response_model=PriceHoldResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create temporary price hold for a flight search quote",
    description="Holds fare price for 15 minutes before booking completion.",
)
async def create_price_hold(
    request: PriceHoldCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PriceHoldResponse:
    hold = await PriceHoldService.create_price_hold(db, current_user.id, request)
    return PriceHoldResponse.model_validate(hold)
