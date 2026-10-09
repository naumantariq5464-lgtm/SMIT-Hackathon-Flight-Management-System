import enum
import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import String, Numeric, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class CancellationType(str, enum.Enum):
    FULL_BOOKING = "FULL_BOOKING"
    PARTIAL_PASSENGERS = "PARTIAL_PASSENGERS"
    AIRLINE_FLIGHT_CANCELLED = "AIRLINE_FLIGHT_CANCELLED"


class Cancellation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cancellations"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cancelled_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cancellation_type: Mapped[CancellationType] = mapped_column(
        Enum(CancellationType, name="cancellation_type_enum", native_enum=False),
        nullable=False,
    )
    affected_passenger_ids: Mapped[str] = mapped_column(Text, nullable=False, default="")  # comma-separated UUIDs
    reason: Mapped[str] = mapped_column(String(255), default="Passenger requested cancellation", nullable=False)
    
    original_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    penalty_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="cancellations")
    refunds: Mapped[List["Refund"]] = relationship("Refund", back_populates="cancellation")
    travel_credits: Mapped[List["TravelCredit"]] = relationship("TravelCredit", back_populates="cancellation")
