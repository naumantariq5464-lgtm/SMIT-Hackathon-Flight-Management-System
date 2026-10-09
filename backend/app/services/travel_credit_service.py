import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.models.travel_credit import TravelCredit, TravelCreditStatus
from app.models.audit_log import AuditAction
from app.services.audit_service import AuditService


class TravelCreditService:
    @staticmethod
    def generate_credit_code() -> str:
        chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"TC-{chars}"

    @staticmethod
    async def issue_credit(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: Decimal,
        currency: str = "USD",
        booking_id: Optional[uuid.UUID] = None,
        cancellation_id: Optional[uuid.UUID] = None,
        validity_days: int = 365,
    ) -> TravelCredit:
        code = TravelCreditService.generate_credit_code()
        expires_at = datetime.now(timezone.utc) + timedelta(days=validity_days)

        credit = TravelCredit(
            user_id=user_id,
            booking_id=booking_id,
            cancellation_id=cancellation_id,
            code=code,
            amount=amount,
            balance=amount,
            currency=currency,
            status=TravelCreditStatus.ACTIVE,
            expires_at=expires_at,
        )
        db.add(credit)
        await db.flush()

        await AuditService.log_action(
            db=db,
            actor_id=user_id,
            action=AuditAction.TRAVEL_CREDIT_ISSUED,
            entity_type="TravelCredit",
            entity_id=str(credit.id),
            new_values={"code": code, "amount": str(amount), "currency": currency},
            context="Travel credit issued",
        )
        return credit

    @staticmethod
    async def list_user_credits(
        db: AsyncSession, user_id: uuid.UUID
    ) -> List[TravelCredit]:
        res = await db.execute(
            select(TravelCredit)
            .where(TravelCredit.user_id == user_id)
            .order_by(TravelCredit.created_at.desc())
        )
        return list(res.scalars().all())
