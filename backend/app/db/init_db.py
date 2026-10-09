import asyncio
from decimal import Decimal
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
import app.models  # Ensures all ORM models are registered with Base.metadata
from app.models.role import Role, RoleEnum
from app.models.user import User, LoyaltyTier
from app.core.config import settings
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


async def init_db(session: AsyncSession) -> None:
    """Initialize database tables and populate seed data."""
    # 1. Seed Roles
    roles_data = [
        (RoleEnum.PASSENGER, "Standard passenger role for searching and booking flights"),
        (RoleEnum.OPS_AGENT, "Operations agent role for managing flight schedules and operations"),
        (RoleEnum.SUPER_ADMIN, "Super administrator with full system management permissions"),
    ]

    for role_name, description in roles_data:
        result = await session.execute(select(Role).where(Role.name == role_name))
        existing_role = result.scalars().first()
        if not existing_role:
            role = Role(name=role_name, description=description)
            session.add(role)
    await session.commit()

    # 2. Seed Super Admin User from Environment Settings
    res_admin_role = await session.execute(select(Role).where(Role.name == RoleEnum.SUPER_ADMIN))
    admin_role = res_admin_role.scalars().first()
    
    if admin_role:
        admin_email = settings.FIRST_SUPERADMIN_EMAIL
        admin_password = settings.FIRST_SUPERADMIN_PASSWORD
        res_admin = await session.execute(select(User).where(User.email == admin_email))
        existing_admin = res_admin.scalars().first()
        if not existing_admin:
            admin_user = User(
                email=admin_email,
                full_name="System Super Administrator",
                hashed_password=get_password_hash(admin_password),
                role_id=admin_role.id,
                is_active=True,
                loyalty_tier=LoyaltyTier.PLATINUM,
            )
            session.add(admin_user)
            await session.commit()
        else:
            # Update password and ensure active super admin
            existing_admin.hashed_password = get_password_hash(admin_password)
            existing_admin.role_id = admin_role.id
            existing_admin.is_active = True
            await session.commit()

    # 3. Seed Default Fare Rules
    from app.models.fare_rule import FareRule, FareType
    from app.models.seat import SeatClass

    default_rules = [
        ("Economy Standard", FareType.BASIC_ECONOMY, SeatClass.ECONOMY, True, Decimal("10.00"), True, Decimal("1.00"), 20),
        ("Business Flexible", FareType.BUSINESS_STANDARD, SeatClass.BUSINESS, True, Decimal("0.00"), True, Decimal("1.50"), 35),
        ("First Luxury Flex", FareType.FIRST_FLEX, SeatClass.FIRST, True, Decimal("0.00"), True, Decimal("2.00"), 50),
    ]

    for name, f_type, s_class, is_ref, penalty, allow_credit, mult, bag in default_rules:
        r_res = await session.execute(select(FareRule).where(FareRule.seat_class == s_class))
        existing_fr = r_res.scalars().first()
        if not existing_fr:
            fr = FareRule(
                name=name,
                fare_type=f_type,
                seat_class=s_class,
                is_refundable=is_ref,
                refund_penalty_percent=penalty,
                travel_credit_eligible=allow_credit,
                multiplier=mult,
                baggage_allowance_kg=bag,
            )
            session.add(fr)
    await session.commit()


async def create_all_tables() -> None:
    """Create all database tables on PostgreSQL/SQLite."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await init_db(session)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(create_all_tables())
