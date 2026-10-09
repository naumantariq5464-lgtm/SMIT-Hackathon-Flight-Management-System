import random
import string
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException, ConflictException
from app.models.flight import Flight, FlightStatus, OverbookingPolicy
from app.models.seat import Seat, SeatClass, SeatStatus
from app.models.fare_rule import FareRule
from app.models.price_hold import PriceHold, HoldStatus
from app.models.seat_hold import SeatHold
from app.models.booking import Booking, BookingStatus
from app.models.booking_passenger import BookingPassenger, PassengerStatus
from app.models.audit_log import AuditAction
from app.schemas.booking import BookingCreate, BookingResponse, BookingPassengerResponse
from app.services.fare_service import FareService
from app.services.price_hold_service import PriceHoldService
from app.services.seat_hold_service import SeatHoldService
from app.services.audit_service import AuditService


class BookingService:
    @staticmethod
    def generate_booking_reference() -> str:
        """Generate a random 6-character uppercase alphanumeric PNR."""
        chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"PNR-{chars}"

    @staticmethod
    async def create_booking(
        db: AsyncSession,
        user_id: uuid.UUID,
        request: BookingCreate,
    ) -> List[Booking]:
        """
        Atomically reserve inventory and book seats for one or more flights (multi-leg)
        with PostgreSQL row-level locks. Prevents overselling under high concurrency.
        """
        flight_reqs = request.flights
        flight_ids = [f.flight_id for f in flight_reqs]

        # 1. Clean up expired seat holds for all requested flights
        for fid in flight_ids:
            await SeatHoldService.cleanup_expired_holds(db, fid)

        # 2. Lock flight rows with SELECT ... FOR UPDATE (order by id to prevent deadlocks)
        flight_stmt = (
            select(Flight)
            .where(Flight.id.in_(flight_ids))
            .order_by(Flight.id)
            .with_for_update()
        )
        res_flights = await db.execute(flight_stmt)
        flights_map = {f.id: f for f in res_flights.scalars().all()}

        if len(flights_map) != len(flight_ids):
            raise NotFoundException("One or more flights not found")

        booking_ref = BookingService.generate_booking_reference()
        created_bookings = []
        now = datetime.now(timezone.utc)

        def to_utc(dt: datetime) -> datetime:
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

        for freq in flight_reqs:
            flight = flights_map[freq.flight_id]

            if flight.status == FlightStatus.CANCELLED:
                raise ConflictException(f"Cannot book seats on cancelled flight {flight.flight_number}")

            dep_time = to_utc(flight.departure_datetime)
            if dep_time <= now:
                raise ConflictException(f"Flight {flight.flight_number} has already departed")

            # 3. Fetch & Validate Fare Rule
            fare_rule = await FareService.get_fare_rule_by_id(db, freq.fare_rule_id)

            # 4. Count passengers per class
            class_counts = {SeatClass.FIRST: 0, SeatClass.BUSINESS: 0, SeatClass.ECONOMY: 0}
            for p in request.passengers:
                class_counts[p.seat_class] += 1

            # 5. Check class booking cutoffs
            hours_to_departure = (dep_time - now).total_seconds() / 3600.0
            if class_counts[SeatClass.FIRST] > 0 and hours_to_departure < flight.first_cutoff_hours:
                raise ConflictException(f"Booking cutoff reached for First Class on {flight.flight_number}")
            if class_counts[SeatClass.BUSINESS] > 0 and hours_to_departure < flight.business_cutoff_hours:
                raise ConflictException(f"Booking cutoff reached for Business Class on {flight.flight_number}")
            if class_counts[SeatClass.ECONOMY] > 0 and hours_to_departure < flight.economy_cutoff_hours:
                raise ConflictException(f"Booking cutoff reached for Economy Class on {flight.flight_number}")

            # 6. Check Inventory & Overbooking Policy per Class
            def calculate_allowed_cap(base_cap: int) -> int:
                if flight.overbooking_policy == OverbookingPolicy.BUFFER_ALLOWED:
                    buffer = int(base_cap * (flight.overbooking_buffer_percent / 100.0))
                    return base_cap + buffer
                return base_cap

            allowed_first = calculate_allowed_cap(flight.first_seats)
            allowed_business = calculate_allowed_cap(flight.business_seats)
            allowed_economy = calculate_allowed_cap(flight.economy_seats)

            avail_first = max(0, allowed_first - flight.booked_first)
            avail_business = max(0, allowed_business - flight.booked_business)
            avail_economy = max(0, allowed_economy - flight.booked_economy)

            # 7. Check Capacity — with PARTIAL_ALLOWED support
            is_partial = request.group_failure_policy == "PARTIAL_ALLOWED"

            if not is_partial:
                # FULL_FAILURE: reject entire booking if any class is short
                if class_counts[SeatClass.FIRST] > avail_first:
                    raise ConflictException(f"Insufficient First Class seats on {flight.flight_number}")
                if class_counts[SeatClass.BUSINESS] > avail_business:
                    raise ConflictException(f"Insufficient Business Class seats on {flight.flight_number}")
                if class_counts[SeatClass.ECONOMY] > avail_economy:
                    raise ConflictException(f"Insufficient Economy Class seats on {flight.flight_number}")
            else:
                # PARTIAL_ALLOWED: cap available slots per class, skip overflow passengers
                avail_slots = {
                    SeatClass.FIRST: avail_first,
                    SeatClass.BUSINESS: avail_business,
                    SeatClass.ECONOMY: avail_economy,
                }
                total_available = sum(min(class_counts[c], avail_slots[c]) for c in avail_slots)
                if total_available == 0:
                    raise ConflictException(f"No seats available in any requested class on {flight.flight_number}")

            # 8. Price Calculation
            price_hold: Optional[PriceHold] = None
            if request.price_hold_id:
                price_hold = await PriceHoldService.get_valid_price_hold(db, request.price_hold_id, user_id)
                price_per_pax = price_hold.held_price_per_passenger
            else:
                price_per_pax = FareService.calculate_fare_price(flight.base_price, fare_rule)

            total_booking_price = price_per_pax * len(request.passengers)

            # 9. Filter passengers for partial booking support
            passengers_to_book = list(request.passengers)
            if is_partial:
                # Only book passengers up to available capacity per class
                class_slots_remaining = {
                    SeatClass.FIRST: avail_first,
                    SeatClass.BUSINESS: avail_business,
                    SeatClass.ECONOMY: avail_economy,
                }
                filtered = []
                for p in passengers_to_book:
                    if class_slots_remaining[p.seat_class] > 0:
                        filtered.append(p)
                        class_slots_remaining[p.seat_class] -= 1
                passengers_to_book = filtered
                total_booking_price = price_per_pax * len(passengers_to_book)

            # 10. Seat Selection and Seat Locking
            specific_seat_ids = [p.seat_id for p in passengers_to_book if p.seat_id is not None]
            selected_seats: List[Seat] = []

            if specific_seat_ids:
                seats_stmt = (
                    select(Seat)
                    .where(Seat.id.in_(specific_seat_ids), Seat.flight_id == flight.id)
                    .with_for_update()
                )
                res_seats = await db.execute(seats_stmt)
                selected_seats = list(res_seats.scalars().all())

                for seat in selected_seats:
                    if seat.status == SeatStatus.BOOKED or seat.status == SeatStatus.BLOCKED:
                        raise ConflictException(f"Seat {seat.seat_number} on {flight.flight_number} is already booked")
                    elif seat.status == SeatStatus.HELD:
                        hold_stmt = select(SeatHold).where(
                            SeatHold.seat_id == seat.id, SeatHold.user_id == user_id, SeatHold.status == HoldStatus.ACTIVE
                        )
                        if not (await db.execute(hold_stmt)).scalars().first():
                            raise ConflictException(f"Seat {seat.seat_number} on {flight.flight_number} is held by another passenger")

            seat_map = {s.id: s for s in selected_seats}

            # 11. Create Booking Record
            booking = Booking(
                booking_reference=booking_ref,
                user_id=user_id,
                flight_id=flight.id,
                fare_rule_id=fare_rule.id,
                price_hold_id=price_hold.id if price_hold else None,
                total_price=total_booking_price,
                currency=flight.currency,
                status=BookingStatus.CONFIRMED,
            )
            db.add(booking)
            await db.flush()

            # 12. Create Booking Passengers & Assign Seats
            booked_class_counts = {SeatClass.FIRST: 0, SeatClass.BUSINESS: 0, SeatClass.ECONOMY: 0}
            for p in passengers_to_book:
                assigned_seat: Optional[Seat] = None
                if p.seat_id and p.seat_id in seat_map:
                    assigned_seat = seat_map[p.seat_id]
                    assigned_seat.status = SeatStatus.BOOKED
                else:
                    avail_seat_stmt = (
                        select(Seat)
                        .where(Seat.flight_id == flight.id, Seat.seat_class == p.seat_class, Seat.status == SeatStatus.AVAILABLE)
                        .order_by(Seat.seat_number.asc())
                        .limit(1)
                        .with_for_update()
                    )
                    avail_seat = (await db.execute(avail_seat_stmt)).scalars().first()
                    if not avail_seat:
                        if is_partial:
                            continue  # Skip this passenger in partial mode
                        raise ConflictException(f"No available physical seats in {p.seat_class.value} class on {flight.flight_number}")

                    seat_upd = update(Seat).where(Seat.id == avail_seat.id, Seat.status == SeatStatus.AVAILABLE).values(status=SeatStatus.BOOKED)
                    if (await db.execute(seat_upd)).rowcount == 0:
                        if is_partial:
                            continue  # Skip in partial mode
                        raise ConflictException(f"Seat {avail_seat.seat_number} claimed concurrently on {flight.flight_number}")
                    assigned_seat = avail_seat

                passenger = BookingPassenger(
                    booking_id=booking.id,
                    seat_id=assigned_seat.id if assigned_seat else None,
                    seat_number=assigned_seat.seat_number if assigned_seat else None,
                    seat_class=p.seat_class,
                    first_name=p.first_name.strip(),
                    last_name=p.last_name.strip(),
                    passport_number=p.passport_number.strip() if p.passport_number else None,
                    ticket_price=price_per_pax,
                    status=PassengerStatus.CONFIRMED,
                )
                db.add(passenger)
                booked_class_counts[p.seat_class] += 1

            flight.booked_first += booked_class_counts[SeatClass.FIRST]
            flight.booked_business += booked_class_counts[SeatClass.BUSINESS]
            flight.booked_economy += booked_class_counts[SeatClass.ECONOMY]
            db.add(flight)

            if price_hold:
                price_hold.status = HoldStatus.CONSUMED
            if specific_seat_ids:
                seat_holds_stmt = select(SeatHold).where(SeatHold.seat_id.in_(specific_seat_ids), SeatHold.user_id == user_id, SeatHold.status == HoldStatus.ACTIVE)
                for sh in (await db.execute(seat_holds_stmt)).scalars().all():
                    sh.status = HoldStatus.CONSUMED

            created_bookings.append(booking)

            await AuditService.log_action(
                db=db,
                actor_id=user_id,
                action=AuditAction.BOOKING_CREATED,
                entity_type="booking",
                entity_id=str(booking.id),
                new_values={"flight_id": str(flight.id), "pnr": booking_ref},
            )

        await db.commit()

        # Eager load relationships for the response
        for b in created_bookings:
            await db.refresh(b, ["passengers", "flight"])

        # Note: We should import EmailService here and send confirmation async
        try:
            from app.services.email_service import EmailService
            from app.models.user import User
            import asyncio
            
            user_stmt = select(User).where(User.id == user_id)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            if user:
                asyncio.create_task(EmailService.send_booking_confirmation(user.email, booking_ref, created_bookings))
        except ImportError:
            pass

        return created_bookings

    @staticmethod
    async def get_booking_by_id(
        db: AsyncSession, booking_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Booking:
        query = (
            select(Booking)
            .options(selectinload(Booking.passengers))
            .where(Booking.id == booking_id)
        )
        if user_id:
            query = query.where(Booking.user_id == user_id)

        result = await db.execute(query)
        booking = result.scalars().first()
        if not booking:
            raise NotFoundException(f"Booking {booking_id} not found")
        return booking

    @staticmethod
    async def list_user_bookings(
        db: AsyncSession, user_id: uuid.UUID
    ) -> List[Booking]:
        query = (
            select(Booking)
            .options(selectinload(Booking.passengers))
            .where(Booking.user_id == user_id)
            .order_by(Booking.created_at.desc())
        )
        res = await db.execute(query)
        return list(res.scalars().all())
