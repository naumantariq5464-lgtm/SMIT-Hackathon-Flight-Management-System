import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin


class AuditAction(str, enum.Enum):
    USER_REGISTERED = "USER_REGISTERED"
    USER_ROLE_UPDATED = "USER_ROLE_UPDATED"
    FLIGHT_CREATED = "FLIGHT_CREATED"
    FLIGHT_UPDATED = "FLIGHT_UPDATED"
    FLIGHT_CANCELLED = "FLIGHT_CANCELLED"
    SEAT_ALLOCATION_CHANGED = "SEAT_ALLOCATION_CHANGED"
    PRICE_HOLD_CREATED = "PRICE_HOLD_CREATED"
    SEAT_HOLD_CREATED = "SEAT_HOLD_CREATED"
    SEAT_HOLD_RELEASED = "SEAT_HOLD_RELEASED"
    BOOKING_CREATED = "BOOKING_CREATED"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    PARTIAL_BOOKING_CANCELLED = "PARTIAL_BOOKING_CANCELLED"
    REFUND_CREATED = "REFUND_CREATED"
    REFUND_STATUS_UPDATED = "REFUND_STATUS_UPDATED"
    TRAVEL_CREDIT_ISSUED = "TRAVEL_CREDIT_ISSUED"
    TRAVEL_CREDIT_USED = "TRAVEL_CREDIT_USED"
    SCHEDULE_CHANGED = "SCHEDULE_CHANGED"
    REBOOKING_CREATED = "REBOOKING_CREATED"
    WAITLIST_JOINED = "WAITLIST_JOINED"


# --- Approval & Autonomy Boundaries ---
# Actions auto-approved (no human sign-off needed):
#   - Standard reminders, in-policy refunds, booking/cancellation by user
#   - BOOKING_CREATED, BOOKING_CANCELLED, REFUND_CREATED (in-policy),
#     PRICE_HOLD_CREATED, SEAT_HOLD_CREATED, TRAVEL_CREDIT_ISSUED, WAITLIST_JOINED
#
# Actions requiring human sign-off:
#   - Schedule-change compensation, denied-boarding compensation,
#     manual fare overrides, out-of-policy refunds
#   - SCHEDULE_CHANGED (with compensation), REBOOKING_CREATED (manual override),
#     REFUND_STATUS_UPDATED (escalated)
ACTIONS_REQUIRING_APPROVAL = {
    AuditAction.SCHEDULE_CHANGED,
    AuditAction.REBOOKING_CREATED,
}


class ApprovalStatus(str, enum.Enum):
    AUTO_APPROVED = "AUTO_APPROVED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AuditLog(Base, UUIDMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    old_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    new_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    context: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Approval & Autonomy Boundary fields
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status_enum", native_enum=False),
        default=ApprovalStatus.AUTO_APPROVED,
        nullable=False,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_id])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])
