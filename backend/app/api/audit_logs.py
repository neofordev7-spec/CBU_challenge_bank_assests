from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from app.core.dependencies import require_auth

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    asset_id: int | None = Query(None),
    action: str | None = Query(None),
    performed_by: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    query = db.query(AuditLog)
    if asset_id:
        query = query.filter(AuditLog.asset_id == asset_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if performed_by:
        query = query.filter(AuditLog.performed_by == performed_by)

    total = query.count()
    items = query.order_by(AuditLog.performed_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/asset/{asset_id}", response_model=list[AuditLogResponse])
def get_asset_audit_logs(asset_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.asset_id == asset_id)
        .order_by(AuditLog.performed_at.desc())
        .all()
    )
    return [AuditLogResponse.model_validate(l) for l in logs]
