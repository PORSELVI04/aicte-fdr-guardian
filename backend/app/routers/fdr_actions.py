from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.audit_log import AuditLog
from app.models.fdr import FDR
from app.models.fdr_action import FDRAction
from app.models.user import User


router = APIRouter(
    prefix="/api/fdr-actions",
    tags=["FDR Actions"],
)


# Request schema for creating an FDR action
class FDRActionCreate(BaseModel):
    fdr_id: int = Field(gt=0)
    action_type: Literal["RENEWAL", "REPLACEMENT", "RELEASE"]
    remarks: str | None = Field(default=None, max_length=1000)


# Request schema for approving or rejecting an action
class FDRActionDecision(BaseModel):
    action_status: Literal["APPROVED", "REJECTED"]
    remarks: str | None = Field(default=None, max_length=1000)


# Convert an FDR action object into a JSON-compatible dictionary
def action_to_dict(action: FDRAction):
    return {
        "id": action.id,
        "fdr_id": action.fdr_id,
        "action_type": action.action_type,
        "action_status": action.action_status,
        "remarks": action.remarks,
        "performed_by": action.performed_by,
        "created_at": (
            action.created_at.isoformat()
            if action.created_at
            else None
        ),
        "decided_by": action.decided_by,
        "decided_at": (
            action.decided_at.isoformat()
            if action.decided_at
            else None
        ),
    }


# Create a new FDR action request
# ADMIN and OFFICER can create requests
@router.post("/", status_code=201)
def create_fdr_action(
    data: FDRActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER")
    ),
):
    fdr = db.get(FDR, data.fdr_id)

    if fdr is None:
        raise HTTPException(
            status_code=404,
            detail="FDR record not found.",
        )

    action = FDRAction(
        fdr_id=data.fdr_id,
        action_type=data.action_type,
        action_status="PENDING",
        remarks=data.remarks,
        performed_by=current_user.username,
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return action_to_dict(action)


# List FDR action requests
# ADMIN, OFFICER and REVIEWER can view requests
@router.get("/")
def list_fdr_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER", "REVIEWER")
    ),
):
    actions = (
        db.query(FDRAction)
        .order_by(FDRAction.created_at.desc())
        .all()
    )

    return [action_to_dict(action) for action in actions]


# Approve or reject an FDR action request
# ADMIN and REVIEWER can make decisions
@router.patch("/{action_id}/decision")
def decide_fdr_action(
    action_id: int,
    data: FDRActionDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "REVIEWER")
    ),
):
    action = db.get(FDRAction, action_id)

    if action is None:
        raise HTTPException(
            status_code=404,
            detail="FDR action request not found.",
        )

    # Prevent an already-decided request from being decided again
    if action.action_status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="This request has already been decided.",
        )

    # Update the FDR action decision
    action.action_status = data.action_status
    action.decided_by = current_user.username
    action.decided_at = datetime.utcnow()

    if data.remarks is not None:
        action.remarks = data.remarks

    # Create an audit log entry for the decision
    audit_entry = AuditLog(
        action=f"FDR_ACTION_{data.action_status}",
        entity_type="FDR_ACTION",
        entity_id=action.id,
        actor=current_user.username,
        details=(
            f"FDR ID: {action.fdr_id}; "
            f"Action type: {action.action_type}; "
            f"Status: {data.action_status}; "
            f"Remarks: {action.remarks or 'None'}"
        ),
    )

    db.add(audit_entry)

    # Save the decision and audit entry in one transaction
    try:
        db.commit()
        db.refresh(action)
    except Exception:
        db.rollback()
        raise

    return action_to_dict(action)