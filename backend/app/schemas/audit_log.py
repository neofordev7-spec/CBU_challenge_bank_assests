from datetime import datetime
from pydantic import BaseModel

from app.schemas.user import UserResponse


class AuditLogResponse(BaseModel):
    id: int
    asset_id: int | None = None
    action: str
    entity_type: str
    entity_id: int
    old_value: str | None = None
    new_value: str | None = None
    description: str
    performed_by: int | None = None
    performed_at: datetime
    user: UserResponse | None = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
