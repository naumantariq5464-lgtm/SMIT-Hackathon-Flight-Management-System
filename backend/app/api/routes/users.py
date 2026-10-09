import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import (
    UserResponse,
    UserProfileUpdateRequest,
    UserUpdateRoleRequest,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get my profile details",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update my profile details",
)
async def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    updated_user = await UserService.update_profile(db, current_user.id, request)
    return UserResponse.model_validate(updated_user)


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users (Super Admin only)",
    dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))],
)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserResponse]:
    skip = (page - 1) * size
    users, total = await UserService.list_users(db, skip=skip, limit=size)
    pages = (total + size - 1) // size if size > 0 else 0
    return PaginatedResponse[UserResponse](
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Assign user role (Super Admin only)",
)
async def update_user_role(
    user_id: uuid.UUID,
    request: UserUpdateRoleRequest,
    current_user: User = Depends(require_role([RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    updated_user = await UserService.update_user_role(
        db=db,
        actor_id=current_user.id,
        target_user_id=user_id,
        role_name=request.role_name,
    )
    return UserResponse.model_validate(updated_user)
