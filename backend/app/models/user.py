import enum
import uuid
from typing import Optional, List
from sqlalchemy import String, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class LoyaltyTier(str, enum.Enum):
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    loyalty_tier: Mapped[LoyaltyTier] = mapped_column(
        Enum(LoyaltyTier, name="loyalty_tier_enum", native_enum=False),
        default=LoyaltyTier.BRONZE,
        nullable=False,
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="user")
    price_holds: Mapped[List["PriceHold"]] = relationship("PriceHold", back_populates="user")
    seat_holds: Mapped[List["SeatHold"]] = relationship("SeatHold", back_populates="user")
    waitlist_entries: Mapped[List["Waitlist"]] = relationship("Waitlist", back_populates="user")
    travel_credits: Mapped[List["TravelCredit"]] = relationship("TravelCredit", back_populates="user")
    refunds: Mapped[List["Refund"]] = relationship("Refund", back_populates="user")
