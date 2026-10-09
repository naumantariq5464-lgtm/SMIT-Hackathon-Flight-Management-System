import enum
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import UUIDMixin, TimestampMixin


class RoleEnum(str, enum.Enum):
    PASSENGER = "passenger"
    OPS_AGENT = "ops_agent"
    SUPER_ADMIN = "super_admin"


class Role(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[RoleEnum] = mapped_column(
        Enum(RoleEnum, name="role_enum", native_enum=False),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="role")
