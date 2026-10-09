import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException, ConflictException
from app.models.flight import Flight, FlightStatus
from app.models.fare_rule import FareRule
from app.models.price_hold import PriceHold, HoldStatus
from app.models.seat import SeatClass
from app.models.audit_log import AuditAction
from app.schemas.price_hold import PriceHoldCreate
from app.services.fare_service import FareService
from app.services.audit_service import AuditService


class PriceHoldService:
    @staticmethod
    async def create_price_hold(
        db: AsyncSession, user_id: uuid.UUID, request: PriceHoldCreate
    ) -> PriceHold:
        # 1. Fetch flight
        res_flight = await db.execute(select(Flight).where(Flight.id == request.flight_id))
        flight = res_flight.scalars().first()
        if not flight:
            raise NotFoundException("Flight not found")
        if flight.status == FlightStatus.CANCELLED:
            raise ConflictException("Cannot hold price on a cancelled flight")

        # 2. Check seat availability for requested class
        if request.seat_class == SeatClass.FIRST:
            available = flight.first_seats - flight.booked_first
        elif request.seat_class == SeatClass.BUSINESS:
            available = flight.business_seats - flight.booked_business
        else:
            available = flight.economy_seats - flight.booked_economy

        if available < request.passenger_count:
            raise ConflictException(
                f"Insufficient seats available in {request.seat_class.value} class (Requested: {request.passenger_count}, Available: {available})"
            )

        # 3. Fetch Fare Rule
        fare_rule = await FareService.get_fare_rule_by_id(db, request.fare_rule_id)
        if fare_rule.seat_class != request.seat_class:
            raise BadRequestException(
                f"Fare rule class ({fare_rule.seat_class.value}) does not match requested class ({request.seat_class.value})"
            )

        price_per_pax = FareService.calculate_fare_price(flight.base_price, fare_rule)
        total_price = price_per_pax * request.passenger_count
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PRICE_HOLD_EXPIRE_MINUTES)

        hold = PriceHold(
            flight_id=flight.id,
            user_id=user_id,
            fare_rule_id=fare_rule.id,
            seat_class=request.seat_class,
            passenger_count=request.passenger_count,
            held_price_per_passenger=price_per_pax,
            total_held_price=total_price,
            currency=flight.currency,
            status=HoldStatus.ACTIVE,
            expires_at=expires_at,
        )
        db.add(hold)
        await db.flush()

        await AuditService.log_action(
            db=db,
            actor_id=user_id,
            action=AuditAction.PRICE_HOLD_CREATED,
            entity_type="PriceHold",
            entity_id=str(hold.id),
            new_values={
                "flight_id": str(flight.id),
                "total_held_price": str(total_price),
                "expires_at": expires_at.isoformat(),
            },
        )
        await db.commit()
        await db.refresh(hold)
        return hold

    @staticmethod
    async def get_valid_price_hold(
        db: AsyncSession, hold_id: uuid.UUID, user_id: uuid.UUID
    ) -> PriceHold:
        res = await db.execute(select(PriceHold).where(PriceHold.id == hold_id, PriceHold.user_id == user_id))
        hold = res.scalars().first()
        if not hold:
            raise NotFoundException("Price hold record not found")

        now = datetime.now(timezone.utc)
        exp_time = hold.expires_at.replace(tzinfo=timezone.utc) if hold.expires_at.tzinfo is None else hold.expires_at
        if exp_time < now or hold.status != HoldStatus.ACTIVE:
            hold.status = HoldStatus.EXPIRED
            await db.commit()
            raise ConflictException("Price hold has expired or is no longer active")

        return hold
