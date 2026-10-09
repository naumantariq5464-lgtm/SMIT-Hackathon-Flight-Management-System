import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.seat import SeatMapResponse
from app.services.seat_service import SeatService

router = APIRouter(prefix="/flights", tags=["Seats"])


@router.get(
    "/{flight_id}/seats",
    response_model=SeatMapResponse,
    summary="Get interactive physical seat map for a flight",
    description="Returns full seat layout (First, Business, Economy) with live statuses (AVAILABLE, HELD, BOOKED, BLOCKED).",
)
async def get_flight_seat_map(
    flight_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SeatMapResponse:
    return await SeatService.get_flight_seat_map(db, flight_id)
