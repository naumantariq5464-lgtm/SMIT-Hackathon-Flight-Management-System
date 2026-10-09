import enum
import uuid
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class SeatClass(str, enum.Enum):
    FIRST = "FIRST"
    BUSINESS = "BUSINESS"
    ECONOMY = "ECONOMY"


class SeatStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"


class Seat(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "seats"

    flight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)
    seat_class: Mapped[SeatClass] = mapped_column(
        Enum(SeatClass, name="seat_class_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    status: Mapped[SeatStatus] = mapped_column(
        Enum(SeatStatus, name="seat_status_enum", native_enum=False),
        default=SeatStatus.AVAILABLE,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint("flight_id", "seat_number", name="uq_flight_seat_number"),
        Index("idx_seats_flight_class_status", "flight_id", "seat_class", "status"),
    )

    # Relationships
    flight: Mapped["Flight"] = relationship("Flight", back_populates="seats")
    seat_holds: Mapped[List["SeatHold"]] = relationship("SeatHold", back_populates="seat")
    passengers: Mapped[List["BookingPassenger"]] = relationship("BookingPassenger", back_populates="seat")
