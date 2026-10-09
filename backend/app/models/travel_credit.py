import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class TravelCreditStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class TravelCredit(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "travel_credits"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cancellation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cancellations.id", ondelete="SET NULL"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    status: Mapped[TravelCreditStatus] = mapped_column(
        Enum(TravelCreditStatus, name="travel_credit_status_enum", native_enum=False),
        default=TravelCreditStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("idx_travel_credits_user_status", "user_id", "status"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="travel_credits")
    booking: Mapped[Optional["Booking"]] = relationship("Booking", back_populates="travel_credits")
    cancellation: Mapped[Optional["Cancellation"]] = relationship("Cancellation", back_populates="travel_credits")
