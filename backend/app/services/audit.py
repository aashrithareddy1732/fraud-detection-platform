import json

from sqlalchemy.orm import Session

from app.models import AuditLog


def record_audit(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict | None = None,
    correlation_id: str | None = None,
) -> None:
    db.add(
        AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details or {}),
            correlation_id=correlation_id,
        )
    )
