import json
import uuid
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_idempotency_key
from app.db.session import get_db
from app.models.user import User
from app.models.idempotency import IdempotencyStatus
from app.schemas.seat_hold import SeatHoldCreate, SeatHoldResponse
from app.schemas.booking import BookingCreate, BookingResponse, BookingPassengerResponse
from app.services.seat_hold_service import SeatHoldService
from app.services.booking_service import BookingService
from app.services.idempotency_service import IdempotencyService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "/hold",
    response_model=SeatHoldResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Hold selected seats for 10 minutes",
    description="Reserves selected physical seats with 10-minute TTL to prevent concurrent conflicts.",
)
async def hold_seats(
    request: SeatHoldCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SeatHoldResponse:
    return await SeatHoldService.hold_seats(db, current_user.id, request)


@router.post(
    "",
    response_model=List[BookingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Atomic multi-leg flight booking checkout with idempotency",
    description="Atomically reserves inventory and books flight tickets for one or more flights. Supports Idempotency-Key header.",
)
async def create_booking(
    request: BookingCreate,
    response: Response,
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # 1. Check idempotency
    idempotency_record = await IdempotencyService.check_or_create(
        db=db,
        user_id=current_user.id,
        endpoint="/bookings",
        idempotency_key=idempotency_key,
        payload=request.model_dump(),
    )

    if idempotency_record and idempotency_record.status == IdempotencyStatus.COMPLETED:
        # Return cached response
        response.status_code = idempotency_record.response_code or 200
        return json.loads(idempotency_record.response_body or "[]")

    # 2. Execute atomic booking
    bookings = await BookingService.create_booking(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    
    res_data = [BookingResponse.model_validate(b).model_dump(mode="json") for b in bookings]

    # 3. Mark idempotency record completed
    if idempotency_record:
        await IdempotencyService.mark_completed(
            db=db,
            idempotency_record=idempotency_record,
            response_code=status.HTTP_201_CREATED,
            response_data=res_data,
        )
        await db.commit()

    return res_data


@router.get(
    "",
    response_model=List[BookingResponse],
    summary="List all bookings for current passenger",
)
async def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[BookingResponse]:
    bookings = await BookingService.list_user_bookings(db, current_user.id)
    return [BookingResponse.model_validate(b) for b in bookings]


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Get booking details by ID",
)
async def get_booking_details(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    booking = await BookingService.get_booking_by_id(db, booking_id, current_user.id)
    return BookingResponse.model_validate(booking)
