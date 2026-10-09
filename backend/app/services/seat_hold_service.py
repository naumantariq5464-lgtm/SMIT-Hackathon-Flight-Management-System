import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException, ConflictException
from app.models.flight import Flight, FlightStatus
from app.models.seat import Seat, SeatStatus
from app.models.seat_hold import SeatHold
from app.models.price_hold import HoldStatus
from app.models.audit_log import AuditAction
from app.schemas.seat_hold import SeatHoldCreate, SeatHoldResponse, SingleSeatHoldItem
from app.services.audit_service import AuditService


class SeatHoldService:
    @staticmethod
    async def cleanup_expired_holds(db: AsyncSession, flight_id: Optional[uuid.UUID] = None) -> int:
        """Find expired active seat holds, mark EXPIRED, and release seats to AVAILABLE."""
        now = datetime.now(timezone.utc)
        query = select(SeatHold).where(
            SeatHold.status == HoldStatus.ACTIVE,
            SeatHold.expires_at < now,
        )
        if flight_id:
            query = query.where(SeatHold.flight_id == flight_id)

        res = await db.execute(query)
        expired_holds = list(res.scalars().all())

        released_count = 0
        for hold in expired_holds:
            hold.status = HoldStatus.EXPIRED
            # Check if seat is currently HELD and release it
            res_seat = await db.execute(select(Seat).where(Seat.id == hold.seat_id))
            seat = res_seat.scalars().first()
            if seat and seat.status == SeatStatus.HELD:
                seat.status = SeatStatus.AVAILABLE
                released_count += 1

        if released_count > 0:
            await db.flush()
        return released_count

    @staticmethod
    async def hold_seats(
        db: AsyncSession, user_id: uuid.UUID, request: SeatHoldCreate
    ) -> SeatHoldResponse:
        """Atomically lock and hold seats for 10 minutes."""
        # 1. Cleanup expired holds first
        await SeatHoldService.cleanup_expired_holds(db, request.flight_id)

        # 2. Check flight
        res_flight = await db.execute(select(Flight).where(Flight.id == request.flight_id))
        flight = res_flight.scalars().first()
        if not flight:
            raise NotFoundException("Flight not found")
        if flight.status == FlightStatus.CANCELLED:
            raise ConflictException("Cannot hold seats on a cancelled flight")

        # 3. Lock seats with SELECT ... FOR UPDATE to avoid race conditions
        query = (
            select(Seat)
            .where(Seat.id.in_(request.seat_ids), Seat.flight_id == request.flight_id)
            .with_for_update()
        )
        res_seats = await db.execute(query)
        seats = list(res_seats.scalars().all())

        if len(seats) != len(request.seat_ids):
            raise NotFoundException("One or more selected seats were not found on this flight")

        # Verify each seat is AVAILABLE
        for seat in seats:
            if seat.status != SeatStatus.AVAILABLE:
                raise ConflictException(
                    f"Seat {seat.seat_number} is not available (Current status: {seat.status.value})"
                )

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.SEAT_HOLD_EXPIRE_MINUTES)
        held_items: List[SingleSeatHoldItem] = []

        for seat in seats:
            seat.status = SeatStatus.HELD
            hold = SeatHold(
                seat_id=seat.id,
                flight_id=flight.id,
                user_id=user_id,
                status=HoldStatus.ACTIVE,
                expires_at=expires_at,
            )
            db.add(hold)
            await db.flush()

            held_items.append(
                SingleSeatHoldItem(
                    hold_id=hold.id,
                    seat_id=seat.id,
                    seat_number=seat.seat_number,
                    status=HoldStatus.ACTIVE,
                    expires_at=expires_at,
                )
            )

        # Audit log
        await AuditService.log_action(
            db=db,
            actor_id=user_id,
            action=AuditAction.SEAT_HOLD_CREATED,
            entity_type="FlightSeats",
            entity_id=str(flight.id),
            new_values={
                "seat_numbers": [s.seat_number for s in seats],
                "expires_at": expires_at.isoformat(),
            },
        )
        await db.commit()

        return SeatHoldResponse(
            flight_id=flight.id,
            user_id=user_id,
            expires_at=expires_at,
            held_seats=held_items,
        )
