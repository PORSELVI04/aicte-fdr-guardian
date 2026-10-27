from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def add_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int,
    actor: str,
    details: str | None = None,
) -> None:
    """Add an audit entry to the current transaction."""
    db.add(
        AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor[:100],
            details=details,
        )
    )