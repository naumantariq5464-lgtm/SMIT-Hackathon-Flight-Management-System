import enum
from decimal import Decimal
from typing import List
from sqlalchemy import String, Boolean, Numeric, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.seat import SeatClass


class FareType(str, enum.Enum):
    BASIC_ECONOMY = "BASIC_ECONOMY"
    FLEXIBLE = "FLEXIBLE"
    BUSINESS_STANDARD = "BUSINESS_STANDARD"
    FIRST_FLEX = "FIRST_FLEX"


class FareRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fare_rules"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    fare_type: Mapped[FareType] = mapped_column(
        Enum(FareType, name="fare_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    seat_class: Mapped[SeatClass] = mapped_column(
        Enum(SeatClass, name="seat_class_enum", native_enum=False),
        default=SeatClass.ECONOMY,
        nullable=False,
    )
    is_refundable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    refund_penalty_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    travel_credit_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    seat_selection_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    change_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    change_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.00"), nullable=False)
    baggage_allowance_kg: Mapped[int] = mapped_column(Integer, default=20, nullable=False)

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="fare_rule")
    price_holds: Mapped[List["PriceHold"]] = relationship("PriceHold", back_populates="fare_rule")
