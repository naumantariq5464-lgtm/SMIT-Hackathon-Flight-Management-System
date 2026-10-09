from typing import Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ConflictException, UnauthorizedException
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.models.role import Role, RoleEnum
from app.models.user import User, LoyaltyTier
from app.models.audit_log import AuditAction
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, request: RegisterRequest) -> User:
        """Register a new user with secure password hash and default PASSENGER role."""
        # 1. Check duplicate email
        res = await db.execute(select(User).where(User.email == request.email.lower()))
        if res.scalars().first():
            raise ConflictException("A user with this email address already exists")

        # 2. Get default PASSENGER role
        res_role = await db.execute(select(Role).where(Role.name == RoleEnum.PASSENGER))
        role = res_role.scalars().first()
        if not role:
            # Create passenger role if not present
            role = Role(name=RoleEnum.PASSENGER, description="Standard passenger role")
            db.add(role)
            await db.flush()

        # 3. Create user
        user = User(
            email=request.email.lower(),
            full_name=request.full_name.strip(),
            hashed_password=get_password_hash(request.password),
            role_id=role.id,
            is_active=True,
            loyalty_tier=LoyaltyTier.BRONZE,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user, attribute_names=["role"])

        # 4. Audit Log
        await AuditService.log_action(
            db=db,
            actor_id=user.id,
            action=AuditAction.USER_REGISTERED,
            entity_type="User",
            entity_id=str(user.id),
            new_values={"email": user.email, "full_name": user.full_name, "role": role.name.value},
            context="User self-registration",
        )
        await db.commit()
        return user

    @staticmethod
    async def login(db: AsyncSession, request: LoginRequest) -> Tuple[TokenResponse, User]:
        """Authenticate user and return access token."""
        query = select(User).options(selectinload(User.role)).where(User.email == request.email.lower())
        res = await db.execute(query)
        user = res.scalars().first()

        if not user or not verify_password(request.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("User account is inactive")

        token = create_access_token(subject=str(user.id))
        token_response = TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        return token_response, user
