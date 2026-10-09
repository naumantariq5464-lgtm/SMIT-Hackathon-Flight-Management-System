import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.audit_log import AuditAction, ApprovalStatus


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    actor_id: Optional[uuid.UUID]
    action: AuditAction
    entity_type: str
    entity_id: str
    old_values: Optional[str]
    new_values: Optional[str]
    context: Optional[str]
    timestamp: datetime
    requires_approval: bool
    approval_status: ApprovalStatus
    approved_by: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)
