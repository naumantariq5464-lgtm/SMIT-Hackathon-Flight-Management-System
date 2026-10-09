import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.cancellation import (
    CancellationRequest,
    PartialPassengerCancellationRequest,
    CancellationResponse,
)
from app.services.cancellation_service import CancellationService

router = APIRouter(prefix="/bookings", tags=["Cancellations"])


@router.post(
    "/{booking_id}/cancel",
    response_model=CancellationResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel entire booking according to fare rules",
    description="Processes full booking cancellation, calculates refund/travel credit based on fare rules, releases all seats, and updates flight inventory.",
)
async def cancel_full_booking(
    booking_id: uuid.UUID,
    request: CancellationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CancellationResponse:
    cancellation = await CancellationService.cancel_full_booking(
        db=db,
        user_id=current_user.id,
        booking_id=booking_id,
        request=request,
    )
    return CancellationResponse.model_validate(cancellation)


@router.post(
    "/{booking_id}/cancel-partial",
    response_model=CancellationResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel selected passengers from a multi-passenger booking",
    description="Cancels only specified passengers, calculates proportional refund/credit, releases their seats, and reprices remaining active passengers.",
)
async def cancel_partial_passengers(
    booking_id: uuid.UUID,
    request: PartialPassengerCancellationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CancellationResponse:
    cancellation = await CancellationService.cancel_partial_passengers(
        db=db,
        user_id=current_user.id,
        booking_id=booking_id,
        request=request,
    )
    return CancellationResponse.model_validate(cancellation)
