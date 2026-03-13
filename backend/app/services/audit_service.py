import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int,
    description: str,
    asset_id: int | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    performed_by: int | None = None,
):
    log = AuditLog(
        asset_id=asset_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=json.dumps(old_value, default=str) if old_value else None,
        new_value=json.dumps(new_value, default=str) if new_value else None,
        description=description,
        performed_by=performed_by,
        performed_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return log
