import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Integer, DateTime, ForeignKey, Enum, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.seat import SeatClass
from app.models.user import LoyaltyTier


class WaitlistStatus(str, enum.Enum):
    PENDING = "PENDING"
    OFFERED = "OFFERED"
    CONVERTED = "CONVERTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Waitlist(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "waitlists"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_class: Mapped[SeatClass] = mapped_column(
        Enum(SeatClass, name="seat_class_enum", native_enum=False),
        nullable=False,
    )
    loyalty_tier: Mapped[LoyaltyTier] = mapped_column(
        Enum(LoyaltyTier, name="loyalty_tier_enum", native_enum=False),
        nullable=False,
    )
    priority_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    
    status: Mapped[WaitlistStatus] = mapped_column(
        Enum(WaitlistStatus, name="waitlist_status_enum", native_enum=False),
        default=WaitlistStatus.PENDING,
        nullable=False,
        index=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_waitlist_flight_class_prio", "flight_id", "requested_class", "priority_score"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="waitlist_entries")
    flight: Mapped["Flight"] = relationship("Flight", back_populates="waitlist_entries")
