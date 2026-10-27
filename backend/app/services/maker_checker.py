from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def enforce_maker_checker(
    db: Session,
    maker_username: str | None,
    current_user: User,
    entity_type: str,
    entity_id: int,
    label: str,
) -> None:
    """
    Prevent a user from deciding an item they created.
    Record blocked attempts in the audit log.
    """
    if not maker_username or maker_username != current_user.username:
        return

    db.add(
        AuditLog(
            action="MAKER_CHECKER_BLOCKED",
            entity_type=entity_type,
            entity_id=entity_id,
            actor=current_user.username,
            details=(
                f"Blocked: {current_user.username} tried to decide "
                f"a {label} they created themselves."
            ),
        )
    )
    db.commit()

    raise HTTPException(
        status_code=403,
        detail=(
            f"Maker-checker rule: you cannot decide a {label} "
            "that you created. Another authorized user must decide it."
        ),
    )
