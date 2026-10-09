import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String, Integer, Numeric, DateTime, ForeignKey, Enum, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class FlightStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    DELAYED = "DELAYED"
    DEPARTED = "DEPARTED"
    ARRIVED = "ARRIVED"
    CANCELLED = "CANCELLED"


class OverbookingPolicy(str, enum.Enum):
    HARD_LIMIT = "HARD_LIMIT"
    BUFFER_ALLOWED = "BUFFER_ALLOWED"


class Flight(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "flights"

    flight_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    destination: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    departure_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    arrival_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    aircraft_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("aircraft.id", ondelete="SET NULL"), nullable=True
    )
    
    status: Mapped[FlightStatus] = mapped_column(
        Enum(FlightStatus, name="flight_status_enum", native_enum=False),
        default=FlightStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    first_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    business_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    economy_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    booked_first: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    booked_business: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    booked_economy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    overbooking_policy: Mapped[OverbookingPolicy] = mapped_column(
        Enum(OverbookingPolicy, name="overbooking_policy_enum", native_enum=False),
        default=OverbookingPolicy.HARD_LIMIT,
        nullable=False,
    )
    overbooking_buffer_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Class-specific cutoff rules (in hours before departure)
    first_cutoff_hours: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    business_cutoff_hours: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    economy_cutoff_hours: Mapped[int] = mapped_column(Integer, default=6, nullable=False)

    __table_args__ = (
        CheckConstraint("arrival_datetime > departure_datetime", name="chk_flight_arrival_after_departure"),
        CheckConstraint("capacity > 0", name="chk_flight_capacity_positive"),
        CheckConstraint("first_seats >= 0", name="chk_flight_first_seats_non_neg"),
        CheckConstraint("business_seats >= 0", name="chk_flight_business_seats_non_neg"),
        CheckConstraint("economy_seats >= 0", name="chk_flight_economy_seats_non_neg"),
        CheckConstraint("booked_first >= 0", name="chk_flight_booked_first_non_neg"),
        CheckConstraint("booked_business >= 0", name="chk_flight_booked_business_non_neg"),
        CheckConstraint("booked_economy >= 0", name="chk_flight_booked_economy_non_neg"),
        CheckConstraint(
            "first_seats + business_seats + economy_seats = capacity",
            name="chk_flight_capacity_breakdown_sum",
        ),
        UniqueConstraint("flight_number", "departure_datetime", name="uq_flight_number_departure"),
        Index("idx_flight_search", "origin", "destination", "departure_datetime", "status"),
    )

    # Relationships
    aircraft: Mapped[Optional["Aircraft"]] = relationship("Aircraft", back_populates="flights")
    seats: Mapped[List["Seat"]] = relationship("Seat", back_populates="flight", cascade="all, delete-orphan")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="flight")
    price_holds: Mapped[List["PriceHold"]] = relationship("PriceHold", back_populates="flight")
    seat_holds: Mapped[List["SeatHold"]] = relationship("SeatHold", back_populates="flight")
    waitlist_entries: Mapped[List["Waitlist"]] = relationship("Waitlist", back_populates="flight")
