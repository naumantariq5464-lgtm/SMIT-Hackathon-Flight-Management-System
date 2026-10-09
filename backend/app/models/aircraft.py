from typing import List
from sqlalchemy import String, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class Aircraft(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "aircraft"

    model: Mapped[str] = mapped_column(String(100), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    first_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    business_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    economy_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint("total_capacity > 0", name="chk_aircraft_total_capacity_positive"),
        CheckConstraint("first_seats >= 0", name="chk_aircraft_first_seats_non_negative"),
        CheckConstraint("business_seats >= 0", name="chk_aircraft_business_seats_non_negative"),
        CheckConstraint("economy_seats >= 0", name="chk_aircraft_economy_seats_non_negative"),
        CheckConstraint(
            "first_seats + business_seats + economy_seats = total_capacity",
            name="chk_aircraft_capacity_sum",
        ),
    )

    # Relationships
    flights: Mapped[List["Flight"]] = relationship("Flight", back_populates="aircraft")
