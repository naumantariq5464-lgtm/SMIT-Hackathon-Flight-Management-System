import json
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog, AuditAction, ApprovalStatus, ACTIONS_REQUIRING_APPROVAL


class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        actor_id: Optional[uuid.UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
        requires_approval: Optional[bool] = None,
    ) -> AuditLog:
        """
        Create a persistent immutable audit log entry.
        
        Approval & Autonomy Boundaries:
        - If `requires_approval` is explicitly set, use that value.
        - Otherwise, auto-detect based on ACTIONS_REQUIRING_APPROVAL set.
        - Sensitive actions (SCHEDULE_CHANGED, REBOOKING_CREATED) are flagged
          as PENDING_APPROVAL by default.
        - All other actions are AUTO_APPROVED.
        """
        # Determine approval requirement
        if requires_approval is None:
            requires_approval = action in ACTIONS_REQUIRING_APPROVAL

        approval_status = (
            ApprovalStatus.PENDING_APPROVAL if requires_approval
            else ApprovalStatus.AUTO_APPROVED
        )

        log_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            old_values=json.dumps(old_values, default=str) if old_values else None,
            new_values=json.dumps(new_values, default=str) if new_values else None,
            context=context,
            requires_approval=requires_approval,
            approval_status=approval_status,
        )
        db.add(log_entry)
        await db.flush()
        return log_entry

    @staticmethod
    async def approve_action(
        db: AsyncSession,
        audit_log_id: uuid.UUID,
        approver_id: uuid.UUID,
    ) -> AuditLog:
        """Mark a pending-approval audit entry as approved by a super-admin."""
        from sqlalchemy import select
        from app.core.exceptions import NotFoundException, ConflictException

        res = await db.execute(select(AuditLog).where(AuditLog.id == audit_log_id))
        log_entry = res.scalars().first()
        if not log_entry:
            raise NotFoundException("Audit log entry not found")

        if log_entry.approval_status != ApprovalStatus.PENDING_APPROVAL:
            raise ConflictException(
                f"Cannot approve: current status is {log_entry.approval_status.value}"
            )

        log_entry.approval_status = ApprovalStatus.APPROVED
        log_entry.approved_by = approver_id
        await db.flush()
        return log_entry

    @staticmethod
    async def reject_action(
        db: AsyncSession,
        audit_log_id: uuid.UUID,
        rejector_id: uuid.UUID,
    ) -> AuditLog:
        """Mark a pending-approval audit entry as rejected."""
        from sqlalchemy import select
        from app.core.exceptions import NotFoundException, ConflictException

        res = await db.execute(select(AuditLog).where(AuditLog.id == audit_log_id))
        log_entry = res.scalars().first()
        if not log_entry:
            raise NotFoundException("Audit log entry not found")

        if log_entry.approval_status != ApprovalStatus.PENDING_APPROVAL:
            raise ConflictException(
                f"Cannot reject: current status is {log_entry.approval_status.value}"
            )

        log_entry.approval_status = ApprovalStatus.REJECTED
        log_entry.approved_by = rejector_id
        await db.flush()
        return log_entry
