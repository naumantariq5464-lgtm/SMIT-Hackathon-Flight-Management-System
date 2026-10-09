import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException, ConflictException, ForbiddenException
from app.models.booking import Booking, BookingStatus
from app.models.booking_passenger import BookingPassenger, PassengerStatus
from app.models.flight import Flight
from app.models.fare_rule import FareRule
from app.models.seat import Seat, SeatStatus, SeatClass
from app.models.cancellation import Cancellation, CancellationType
from app.models.audit_log import AuditAction
from app.schemas.cancellation import CancellationRequest, PartialPassengerCancellationRequest
from app.services.refund_service import RefundService
from app.services.travel_credit_service import TravelCreditService
from app.services.audit_service import AuditService


class CancellationService:
    @staticmethod
    async def cancel_full_booking(
        db: AsyncSession,
        user_id: uuid.UUID,
        booking_id: uuid.UUID,
        request: CancellationRequest,
        is_admin: bool = False,
    ) -> Cancellation:
        """Cancel an entire booking according to fare rules."""
        # 1. Load booking with flight, fare rule, passengers
        query = (
            select(Booking)
            .options(
                selectinload(Booking.passengers),
                selectinload(Booking.fare_rule),
            )
            .where(Booking.id == booking_id)
            .with_for_update()
        )
        res = await db.execute(query)
        booking = res.scalars().first()

        if not booking:
            raise NotFoundException("Booking not found")

        if not is_admin and booking.user_id != user_id:
            raise ForbiddenException("You cannot cancel another user's booking")

        if booking.status in (BookingStatus.CANCELLED, BookingStatus.EXPIRED):
            raise ConflictException("Booking is already cancelled or expired")

        # 2. Lock flight
        res_flight = await db.execute(
            select(Flight).where(Flight.id == booking.flight_id).with_for_update()
        )
        flight = res_flight.scalars().first()

        # 3. Calculate refund/credit based on fare rule
        fare_rule = booking.fare_rule
        original_total = booking.total_price
        refund_amount = Decimal("0.00")
        credit_amount = Decimal("0.00")
        penalty_amount = Decimal("0.00")

        if fare_rule.is_refundable:
            penalty_rate = fare_rule.refund_penalty_percent / Decimal("100.00")
            penalty_amount = Decimal(round(original_total * penalty_rate, 2))
            refund_amount = original_total - penalty_amount
        elif fare_rule.travel_credit_eligible:
            credit_amount = original_total
        else:
            # Non-refundable, non-credit
            penalty_amount = original_total

        # 4. Release seats and update flight inventory
        active_passengers = [p for p in booking.passengers if p.status == PassengerStatus.CONFIRMED]
        seat_ids_to_release = [p.seat_id for p in active_passengers if p.seat_id is not None]

        if seat_ids_to_release:
            res_seats = await db.execute(
                select(Seat).where(Seat.id.in_(seat_ids_to_release)).with_for_update()
            )
            for seat in res_seats.scalars().all():
                seat.status = SeatStatus.AVAILABLE

        # Adjust flight counts
        for p in active_passengers:
            p.status = PassengerStatus.CANCELLED
            if p.seat_class == SeatClass.FIRST:
                flight.booked_first = max(0, flight.booked_first - 1)
            elif p.seat_class == SeatClass.BUSINESS:
                flight.booked_business = max(0, flight.booked_business - 1)
            else:
                flight.booked_economy = max(0, flight.booked_economy - 1)

        booking.status = BookingStatus.CANCELLED

        # 5. Create Cancellation Record
        affected_pax_ids = ",".join([str(p.id) for p in active_passengers])
        cancellation = Cancellation(
            booking_id=booking.id,
            cancelled_by_user_id=user_id,
            cancellation_type=CancellationType.FULL_BOOKING,
            affected_passenger_ids=affected_pax_ids,
            reason=request.reason,
            original_amount=original_total,
            refund_amount=refund_amount,
            credit_amount=credit_amount,
            penalty_amount=penalty_amount,
            currency=booking.currency,
        )
        db.add(cancellation)
        await db.flush()

        # 6. Issue Refund or Travel Credit
        if refund_amount > Decimal("0.00"):
            await RefundService.create_refund(
                db=db,
                user_id=booking.user_id,
                booking_id=booking.id,
                amount=refund_amount,
                currency=booking.currency,
                reason=f"Full booking cancellation: {request.reason}",
                cancellation_id=cancellation.id,
            )

        if credit_amount > Decimal("0.00"):
            await TravelCreditService.issue_credit(
                db=db,
                user_id=booking.user_id,
                amount=credit_amount,
                currency=booking.currency,
                booking_id=booking.id,
                cancellation_id=cancellation.id,
            )

        # 7. Audit log
        await AuditService.log_action(
            db=db,
            actor_id=user_id,
            action=AuditAction.BOOKING_CANCELLED,
            entity_type="Booking",
            entity_id=str(booking.id),
            new_values={
                "refund_amount": str(refund_amount),
                "credit_amount": str(credit_amount),
                "penalty_amount": str(penalty_amount),
            },
            context=f"Full booking cancelled: {request.reason}",
        )
        await db.commit()
        
        # 8. Send Email
        try:
            from app.services.email_service import EmailService
            from app.models.user import User
            import asyncio
            
            user_stmt = select(User).where(User.id == booking.user_id)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            if user:
                asyncio.create_task(EmailService.send_cancellation_receipt(
                    user.email, booking.booking_reference, float(refund_amount), float(credit_amount)
                ))
        except ImportError:
            pass
            
        return cancellation

    @staticmethod
    async def cancel_partial_passengers(
        db: AsyncSession,
        user_id: uuid.UUID,
        booking_id: uuid.UUID,
        request: PartialPassengerCancellationRequest,
        is_admin: bool = False,
    ) -> Cancellation:
        """Cancel only selected passengers from a multi-passenger booking."""
        query = (
            select(Booking)
            .options(
                selectinload(Booking.passengers),
                selectinload(Booking.fare_rule),
            )
            .where(Booking.id == booking_id)
            .with_for_update()
        )
        res = await db.execute(query)
        booking = res.scalars().first()

        if not booking:
            raise NotFoundException("Booking not found")

        if not is_admin and booking.user_id != user_id:
            raise ForbiddenException("You cannot cancel another user's booking")

        if booking.status == BookingStatus.CANCELLED:
            raise ConflictException("Booking is already completely cancelled")

        # Find target passengers
        target_pax = [p for p in booking.passengers if p.id in request.passenger_ids and p.status == PassengerStatus.CONFIRMED]
        if not target_pax:
            raise NotFoundException("No active passengers found matching the requested passenger IDs")

        # Lock flight
        res_flight = await db.execute(
            select(Flight).where(Flight.id == booking.flight_id).with_for_update()
        )
        flight = res_flight.scalars().first()

        # Calculate proportional amounts
        cancelled_original = sum(p.ticket_price for p in target_pax)
        fare_rule = booking.fare_rule
        refund_amount = Decimal("0.00")
        credit_amount = Decimal("0.00")
        penalty_amount = Decimal("0.00")

        if fare_rule.is_refundable:
            penalty_rate = fare_rule.refund_penalty_percent / Decimal("100.00")
            penalty_amount = Decimal(round(cancelled_original * penalty_rate, 2))
            refund_amount = cancelled_original - penalty_amount
        elif fare_rule.travel_credit_eligible:
            credit_amount = cancelled_original
        else:
            penalty_amount = cancelled_original

        # Release seats
        seat_ids_to_release = [p.seat_id for p in target_pax if p.seat_id is not None]
        if seat_ids_to_release:
            res_seats = await db.execute(
                select(Seat).where(Seat.id.in_(seat_ids_to_release)).with_for_update()
            )
            for seat in res_seats.scalars().all():
                seat.status = SeatStatus.AVAILABLE

        # Adjust inventory and passenger statuses
        for p in target_pax:
            p.status = PassengerStatus.CANCELLED
            if p.seat_class == SeatClass.FIRST:
                flight.booked_first = max(0, flight.booked_first - 1)
            elif p.seat_class == SeatClass.BUSINESS:
                flight.booked_business = max(0, flight.booked_business - 1)
            else:
                flight.booked_economy = max(0, flight.booked_economy - 1)

        # Update remaining booking state
        remaining_confirmed = [p for p in booking.passengers if p.status == PassengerStatus.CONFIRMED]
        if len(remaining_confirmed) == 0:
            booking.status = BookingStatus.CANCELLED
            booking.total_price = Decimal("0.00")
        else:
            booking.status = BookingStatus.PARTIALLY_CANCELLED
            booking.total_price = sum(p.ticket_price for p in remaining_confirmed)

        affected_pax_ids = ",".join([str(p.id) for p in target_pax])
        cancellation = Cancellation(
            booking_id=booking.id,
            cancelled_by_user_id=user_id,
            cancellation_type=CancellationType.PARTIAL_PASSENGERS,
            affected_passenger_ids=affected_pax_ids,
            reason=request.reason,
            original_amount=cancelled_original,
            refund_amount=refund_amount,
            credit_amount=credit_amount,
            penalty_amount=penalty_amount,
            currency=booking.currency,
        )
        db.add(cancellation)
        await db.flush()

        if refund_amount > Decimal("0.00"):
            await RefundService.create_refund(
                db=db,
                user_id=booking.user_id,
                booking_id=booking.id,
                amount=refund_amount,
                currency=booking.currency,
                reason=f"Partial passenger cancellation: {request.reason}",
                cancellation_id=cancellation.id,
            )

        if credit_amount > Decimal("0.00"):
            await TravelCreditService.issue_credit(
                db=db,
                user_id=booking.user_id,
                amount=credit_amount,
                currency=booking.currency,
                booking_id=booking.id,
                cancellation_id=cancellation.id,
            )

        await AuditService.log_action(
            db=db,
            actor_id=user_id,
            action=AuditAction.PARTIAL_BOOKING_CANCELLED,
            entity_type="Booking",
            entity_id=str(booking.id),
            new_values={
                "cancelled_passengers": affected_pax_ids,
                "refund_amount": str(refund_amount),
                "credit_amount": str(credit_amount),
                "remaining_total": str(booking.total_price),
            },
            context=f"Partial cancellation: {request.reason}",
        )
        await db.commit()

        # Send Email
        try:
            from app.services.email_service import EmailService
            from app.models.user import User
            import asyncio
            
            user_stmt = select(User).where(User.id == booking.user_id)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            if user:
                asyncio.create_task(EmailService.send_cancellation_receipt(
                    user.email, booking.booking_reference, float(refund_amount), float(credit_amount)
                ))
        except ImportError:
            pass

        return cancellation
