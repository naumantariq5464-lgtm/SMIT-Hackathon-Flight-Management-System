from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.waitlist import WaitlistJoinRequest, WaitlistResponse
from app.services.waitlist_service import WaitlistService

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post(
    "",
    response_model=WaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join flight waitlist with priority calculation",
    description="Registers passenger on the waitlist for a full flight or class with priority scored by loyalty tier and class.",
)
async def join_waitlist(
    request: WaitlistJoinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WaitlistResponse:
    entry = await WaitlistService.join_waitlist(db, current_user, request)
    return WaitlistResponse.model_validate(entry)


@router.get(
    "/me",
    response_model=List[WaitlistResponse],
    summary="List all waitlist entries for current user",
)
async def get_my_waitlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[WaitlistResponse]:
    entries = await WaitlistService.list_user_waitlist(db, current_user.id)
    return [WaitlistResponse.model_validate(e) for e in entries]
