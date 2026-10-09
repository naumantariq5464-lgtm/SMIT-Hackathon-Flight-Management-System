import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.role import RoleEnum
from app.models.user import LoyaltyTier


class UserRoleResponse(BaseModel):
    id: uuid.UUID
    name: RoleEnum
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRoleResponse
    loyalty_tier: LoyaltyTier
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRoleRequest(BaseModel):
    role_name: RoleEnum


class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    loyalty_tier: Optional[LoyaltyTier] = None
