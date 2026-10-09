import uuid
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException
from app.models.refund import Refund, RefundStatus
from app.models.audit_log import AuditAction
from app.services.audit_service import AuditService


class RefundService:
    @staticmethod
    async def create_refund(
        db: AsyncSession,
        user_id: uuid.UUID,
        booking_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        reason: str,
        cancellation_id: Optional[uuid.UUID] = None,
    ) -> Refund:
        refund = Refund(
            user_id=user_id,
            booking_id=booking_id,
            cancellation_id=cancellation_id,
            amount=amount,
            currency=currency,
            status=RefundStatus.PENDING,
            reason=reason,
        )
        db.add(refund)
        await db.flush()

        await AuditService.log_action(
            db=db,
            actor_id=user_id,
            action=AuditAction.REFUND_CREATED,
            entity_type="Refund",
            entity_id=str(refund.id),
            new_values={"amount": str(amount), "currency": currency, "status": refund.status.value},
            context="Refund record initiated",
        )
        return refund

    @staticmethod
    async def update_refund_status(
        db: AsyncSession,
        actor_id: uuid.UUID,
        refund_id: uuid.UUID,
        new_status: RefundStatus,
    ) -> Refund:
        res = await db.execute(select(Refund).where(Refund.id == refund_id))
        refund = res.scalars().first()
        if not refund:
            raise NotFoundException(f"Refund {refund_id} not found")

        old_status = refund.status.value
        refund.status = new_status
        await db.flush()

        await AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.REFUND_STATUS_UPDATED,
            entity_type="Refund",
            entity_id=str(refund.id),
            old_values={"status": old_status},
            new_values={"status": new_status.value},
            context="Refund status transition",
        )
        await db.commit()
        return refund

    @staticmethod
    async def list_user_refunds(
        db: AsyncSession, user_id: uuid.UUID
    ) -> List[Refund]:
        res = await db.execute(
            select(Refund)
            .where(Refund.user_id == user_id)
            .order_by(Refund.created_at.desc())
        )
        return list(res.scalars().all())

    @staticmethod
    async def list_all_refunds(
        db: AsyncSession, skip: int = 0, limit: int = 50
    ) -> Tuple[List[Refund], int]:
        total = await db.scalar(select(func.count(Refund.id))) or 0
        res = await db.execute(
            select(Refund)
            .order_by(Refund.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(res.scalars().all()), total
