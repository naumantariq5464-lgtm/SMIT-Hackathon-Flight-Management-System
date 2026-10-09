import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.refund import RefundResponse, RefundStatusUpdateRequest
from app.services.refund_service import RefundService

router = APIRouter(prefix="/refunds", tags=["Refunds"])


@router.get(
    "/me",
    response_model=List[RefundResponse],
    summary="List all refunds for current passenger",
)
async def get_my_refunds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RefundResponse]:
    refunds = await RefundService.list_user_refunds(db, current_user.id)
    return [RefundResponse.model_validate(r) for r in refunds]


@router.get(
    "",
    response_model=PaginatedResponse[RefundResponse],
    summary="List all system refunds (Ops Agent / Super Admin)",
    dependencies=[Depends(require_role([RoleEnum.OPS_AGENT, RoleEnum.SUPER_ADMIN]))],
)
async def list_all_refunds(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[RefundResponse]:
    skip = (page - 1) * size
    refunds, total = await RefundService.list_all_refunds(db, skip=skip, limit=size)
    pages = (total + size - 1) // size if size > 0 else 0
    return PaginatedResponse[RefundResponse](
        items=[RefundResponse.model_validate(r) for r in refunds],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.patch(
    "/{refund_id}/status",
    response_model=RefundResponse,
    summary="Update refund processing status (Ops Agent / Super Admin)",
)
async def update_refund_status(
    refund_id: uuid.UUID,
    request: RefundStatusUpdateRequest,
    current_user: User = Depends(require_role([RoleEnum.OPS_AGENT, RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> RefundResponse:
    updated = await RefundService.update_refund_status(
        db=db,
        actor_id=current_user.id,
        refund_id=refund_id,
        new_status=request.status,
    )
    return RefundResponse.model_validate(updated)
