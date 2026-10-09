import enum
import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import String, Numeric, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PARTIALLY_CANCELLED = "PARTIALLY_CANCELLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Booking(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bookings"

    booking_reference: Mapped[str] = mapped_column(String(12), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    flight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flights.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fare_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fare_rules.id", ondelete="RESTRICT"), nullable=False
    )
    price_hold_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("price_holds.id", ondelete="SET NULL"), nullable=True
    )
    
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status_enum", native_enum=False),
        default=BookingStatus.CONFIRMED,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_bookings_user_status", "user_id", "status"),
        Index("uq_booking_reference_flight", "booking_reference", "flight_id", unique=True),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookings")
    flight: Mapped["Flight"] = relationship("Flight", back_populates="bookings")
    fare_rule: Mapped["FareRule"] = relationship("FareRule", back_populates="bookings")
    passengers: Mapped[List["BookingPassenger"]] = relationship(
        "BookingPassenger", back_populates="booking", cascade="all, delete-orphan", lazy="selectin"
    )
    cancellations: Mapped[List["Cancellation"]] = relationship("Cancellation", back_populates="booking")
    refunds: Mapped[List["Refund"]] = relationship("Refund", back_populates="booking")
    travel_credits: Mapped[List["TravelCredit"]] = relationship("TravelCredit", back_populates="booking")
