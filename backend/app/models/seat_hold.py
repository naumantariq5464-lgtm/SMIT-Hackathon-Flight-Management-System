import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.price_hold import HoldStatus


class SeatHold(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "seat_holds"

    seat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[HoldStatus] = mapped_column(
        Enum(HoldStatus, name="hold_status_enum", native_enum=False),
        default=HoldStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("idx_seat_holds_seat_status", "seat_id", "status", "expires_at"),
    )

    # Relationships
    seat: Mapped["Seat"] = relationship("Seat", back_populates="seat_holds")
    flight: Mapped["Flight"] = relationship("Flight", back_populates="seat_holds")
    user: Mapped["User"] = relationship("User", back_populates="seat_holds")
