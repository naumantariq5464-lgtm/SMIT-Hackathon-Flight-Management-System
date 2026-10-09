import enum
import uuid
from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class IdempotencyStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IdempotencyKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    status: Mapped[IdempotencyStatus] = mapped_column(
        Enum(IdempotencyStatus, name="idempotency_status_enum", native_enum=False),
        default=IdempotencyStatus.IN_PROGRESS,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "key", "endpoint", name="uq_user_idempotency_key_endpoint"),
    )
