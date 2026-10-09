import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, BadRequestException
from app.models.role import Role, RoleEnum
from app.models.user import User
from app.models.audit_log import AuditAction
from app.schemas.user import UserProfileUpdateRequest
from app.services.audit_service import AuditService


class UserService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
        query = select(User).options(selectinload(User.role)).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalars().first()
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        return user

    @staticmethod
    async def update_profile(
        db: AsyncSession, user_id: uuid.UUID, request: UserProfileUpdateRequest
    ) -> User:
        user = await UserService.get_user_by_id(db, user_id)
        old_values = {"full_name": user.full_name, "loyalty_tier": user.loyalty_tier.value}

        if request.full_name is not None:
            user.full_name = request.full_name.strip()
        if request.loyalty_tier is not None:
            user.loyalty_tier = request.loyalty_tier

        await db.flush()
        await db.refresh(user, attribute_names=["role"])
        await db.commit()
        return user

    @staticmethod
    async def update_user_role(
        db: AsyncSession,
        actor_id: uuid.UUID,
        target_user_id: uuid.UUID,
        role_name: RoleEnum,
    ) -> User:
        user = await UserService.get_user_by_id(db, target_user_id)
        res_role = await db.execute(select(Role).where(Role.name == role_name))
        role = res_role.scalars().first()
        if not role:
            raise NotFoundException(f"Role {role_name.value} not found")

        old_role = user.role.name.value if user.role else None
        user.role_id = role.id
        await db.flush()
        await db.refresh(user, attribute_names=["role"])

        await AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.USER_ROLE_UPDATED,
            entity_type="User",
            entity_id=str(user.id),
            old_values={"role": old_role},
            new_values={"role": role.name.value},
            context="Admin role update",
        )
        await db.commit()
        return user

    @staticmethod
    async def list_users(
        db: AsyncSession, skip: int = 0, limit: int = 50
    ) -> Tuple[List[User], int]:
        total = await db.scalar(select(func.count(User.id))) or 0
        query = (
            select(User)
            .options(selectinload(User.role))
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(query)
        users = list(res.scalars().all())
        return users, total
