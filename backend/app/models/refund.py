import enum
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class RefundStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Refund(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "refunds"

    cancellation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cancellations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    status: Mapped[RefundStatus] = mapped_column(
        Enum(RefundStatus, name="refund_status_enum", native_enum=False),
        default=RefundStatus.PENDING,
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    cancellation: Mapped[Optional["Cancellation"]] = relationship("Cancellation", back_populates="refunds")
    booking: Mapped["Booking"] = relationship("Booking", back_populates="refunds")
    user: Mapped["User"] = relationship("User", back_populates="refunds")
