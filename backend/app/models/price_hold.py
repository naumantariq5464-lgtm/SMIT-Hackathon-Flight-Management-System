import enum
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.seat import SeatClass


class HoldStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CONSUMED = "CONSUMED"
    RELEASED = "RELEASED"


class PriceHold(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "price_holds"

    flight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fare_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fare_rules.id", ondelete="RESTRICT"), nullable=False
    )
    seat_class: Mapped[SeatClass] = mapped_column(
        Enum(SeatClass, name="seat_class_enum", native_enum=False),
        nullable=False,
    )
    passenger_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    held_price_per_passenger: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_held_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    status: Mapped[HoldStatus] = mapped_column(
        Enum(HoldStatus, name="hold_status_enum", native_enum=False),
        default=HoldStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("idx_price_holds_user_status", "user_id", "status", "expires_at"),
    )

    # Relationships
    flight: Mapped["Flight"] = relationship("Flight", back_populates="price_holds")
    user: Mapped["User"] = relationship("User", back_populates="price_holds")
    fare_rule: Mapped["FareRule"] = relationship("FareRule", back_populates="price_holds")
