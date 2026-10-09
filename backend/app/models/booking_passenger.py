import enum
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.seat import SeatClass


class PassengerStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class BookingPassenger(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "booking_passengers"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seat_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seats.id", ondelete="SET NULL"), nullable=True, index=True
    )
    seat_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    seat_class: Mapped[SeatClass] = mapped_column(
        Enum(SeatClass, name="seat_class_enum", native_enum=False),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    passport_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ticket_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    status: Mapped[PassengerStatus] = mapped_column(
        Enum(PassengerStatus, name="passenger_status_enum", native_enum=False),
        default=PassengerStatus.CONFIRMED,
        nullable=False,
        index=True,
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="passengers")
    seat: Mapped[Optional["Seat"]] = relationship("Seat", back_populates="passengers")
