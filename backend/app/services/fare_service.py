import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.fare_rule import FareRule, FareType
from app.models.seat import SeatClass
from app.models.flight import Flight
from app.schemas.fare import FareRuleCreate


class FareService:
    @staticmethod
    async def list_fare_rules(
        db: AsyncSession, seat_class: Optional[SeatClass] = None
    ) -> List[FareRule]:
        query = select(FareRule)
        if seat_class:
            query = query.where(FareRule.seat_class == seat_class)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_fare_rule_by_id(db: AsyncSession, fare_rule_id: uuid.UUID) -> FareRule:
        result = await db.execute(select(FareRule).where(FareRule.id == fare_rule_id))
        rule = result.scalars().first()
        if not rule:
            raise NotFoundException(f"Fare rule {fare_rule_id} not found")
        return rule

    @staticmethod
    async def create_fare_rule(db: AsyncSession, request: FareRuleCreate) -> FareRule:
        rule = FareRule(
            name=request.name,
            fare_type=request.fare_type,
            seat_class=request.seat_class,
            is_refundable=request.is_refundable,
            refund_penalty_percent=request.refund_penalty_percent,
            travel_credit_eligible=request.travel_credit_eligible,
            seat_selection_allowed=request.seat_selection_allowed,
            change_allowed=request.change_allowed,
            change_fee=request.change_fee,
            multiplier=request.multiplier,
            baggage_allowance_kg=request.baggage_allowance_kg,
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    def calculate_fare_price(base_price: Decimal, fare_rule: FareRule) -> Decimal:
        """Calculate final ticket price using the fare rule multiplier."""
        raw_price = base_price * fare_rule.multiplier
        return Decimal(round(raw_price, 2))
