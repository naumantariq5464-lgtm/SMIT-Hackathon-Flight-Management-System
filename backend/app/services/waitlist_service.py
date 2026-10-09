import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException, ConflictException
from app.models.flight import Flight, FlightStatus
from app.models.user import User, LoyaltyTier
from app.models.seat import SeatClass
from app.models.waitlist import Waitlist, WaitlistStatus
from app.models.audit_log import AuditAction
from app.schemas.waitlist import WaitlistJoinRequest
from app.services.audit_service import AuditService


class WaitlistService:
    @staticmethod
    def calculate_priority_score(loyalty_tier: LoyaltyTier, seat_class: SeatClass) -> int:
        """Calculate weighted priority score."""
        tier_weights = {
            LoyaltyTier.PLATINUM: 400,
            LoyaltyTier.GOLD: 300,
            LoyaltyTier.SILVER: 200,
            LoyaltyTier.BRONZE: 100,
        }
        class_weights = {
            SeatClass.FIRST: 300,
            SeatClass.BUSINESS: 200,
            SeatClass.ECONOMY: 100,
        }
        return tier_weights.get(loyalty_tier, 100) + class_weights.get(seat_class, 100)

    @staticmethod
    async def join_waitlist(
        db: AsyncSession, user: User, request: WaitlistJoinRequest
    ) -> Waitlist:
        """Join waitlist for a full flight or requested class."""
        # 1. Fetch flight
        res_flight = await db.execute(select(Flight).where(Flight.id == request.flight_id))
        flight = res_flight.scalars().first()
        if not flight:
            raise NotFoundException("Flight not found")

        if flight.status == FlightStatus.CANCELLED:
            raise ConflictException("Cannot waitlist for a cancelled flight")

        # 2. Check if already on waitlist
        res_existing = await db.execute(
            select(Waitlist).where(
                Waitlist.user_id == user.id,
                Waitlist.flight_id == flight.id,
                Waitlist.requested_class == request.requested_class,
                Waitlist.status == WaitlistStatus.PENDING,
            )
        )
        if res_existing.scalars().first():
            raise ConflictException("You are already active on the waitlist for this flight class")

        # 3. Calculate priority score
        priority = WaitlistService.calculate_priority_score(user.loyalty_tier, request.requested_class)

        waitlist_entry = Waitlist(
            user_id=user.id,
            flight_id=flight.id,
            requested_class=request.requested_class,
            loyalty_tier=user.loyalty_tier,
            priority_score=priority,
            status=WaitlistStatus.PENDING,
        )
        db.add(waitlist_entry)
        await db.flush()

        # 4. Audit Log
        await AuditService.log_action(
            db=db,
            actor_id=user.id,
            action=AuditAction.WAITLIST_JOINED,
            entity_type="Waitlist",
            entity_id=str(waitlist_entry.id),
            new_values={
                "flight_id": str(flight.id),
                "requested_class": request.requested_class.value,
                "priority_score": priority,
            },
            context="Passenger joined waitlist",
        )
        await db.commit()
        await db.refresh(waitlist_entry)
        return waitlist_entry

    @staticmethod
    async def list_user_waitlist(
        db: AsyncSession, user_id: uuid.UUID
    ) -> List[Waitlist]:
        res = await db.execute(
            select(Waitlist)
            .where(Waitlist.user_id == user_id)
            .order_by(Waitlist.joined_at.desc())
        )
        return list(res.scalars().all())
