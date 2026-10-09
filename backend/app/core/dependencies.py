import uuid
from typing import List, Optional
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.role import Role, RoleEnum
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate Bearer JWT token and return active authenticated user."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authentication token is required")

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired authentication token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload missing subject identifier")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Malformed user identifier in token")

    query = select(User).options(selectinload(User.role)).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise UnauthorizedException("User associated with token does not exist")

    if not user.is_active:
        raise ForbiddenException("User account is inactive")

    return user


def require_role(allowed_roles: List[RoleEnum]):
    """Role-based access control dependency factory."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role or current_user.role.name not in allowed_roles:
            raise ForbiddenException(
                f"Action requires one of the following roles: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker


async def get_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> Optional[str]:
    """Extract optional Idempotency-Key header."""
    return idempotency_key
