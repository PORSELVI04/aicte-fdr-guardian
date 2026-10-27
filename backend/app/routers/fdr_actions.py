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
from app.services.maker_checker import enforce_maker_checker


router = APIRouter(
    prefix="/api/fdr-actions",
    tags=["FDR Actions"],
)


class FDRActionCreate(BaseModel):
    fdr_id: int
    action_type: Literal["RENEWAL", "REPLACEMENT", "RELEASE"]
    remarks: str | None = Field(default=None, max_length=1000)


class FDRActionDecision(BaseModel):
    action_status: Literal["APPROVED", "REJECTED"]
    remarks: str | None = Field(default=None, max_length=1000)


# Outcomes applied to an FDR when an action is approved.
# (administrative_status, validity_status or None to leave unchanged)
APPROVED_OUTCOMES = {
    "RENEWAL": ("RENEWAL_APPROVED", None),
    "REPLACEMENT": ("REPLACEMENT_APPROVED", None),
    "RELEASE": ("RELEASED", "RELEASED"),
}


def apply_approved_action(fdr: FDR, action_type: str) -> str:
    """Update the FDR after approval and describe the change."""

    if action_type not in APPROVED_OUTCOMES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported FDR action type.",
        )

    new_admin_status, new_validity_status = APPROVED_OUTCOMES[
        action_type
    ]

    old_admin_status = fdr.administrative_status
    old_validity_status = fdr.validity_status

    fdr.administrative_status = new_admin_status

    if new_validity_status is not None:
        fdr.validity_status = new_validity_status

    return (
        f"administrative_status: {old_admin_status} -> "
        f"{fdr.administrative_status}; "
        f"validity_status: {old_validity_status} -> "
        f"{fdr.validity_status}"
    )


def action_to_dict(action: FDRAction) -> dict:
    """Convert an FDR action into a JSON-compatible dictionary."""

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


# Create a new FDR action request.
# ADMIN and OFFICER can create requests.
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

    if fdr.validity_status == "RELEASED":
        raise HTTPException(
            status_code=409,
            detail="This FDR has already been released.",
        )

    duplicate_pending = (
        db.query(FDRAction)
        .filter(
            FDRAction.fdr_id == data.fdr_id,
            FDRAction.action_type == data.action_type,
            FDRAction.action_status == "PENDING",
        )
        .first()
    )

    if duplicate_pending is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A pending {data.action_type} request already exists "
                "for this FDR."
            ),
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


# List FDR action requests.
# ADMIN, OFFICER and REVIEWER can view requests.
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


# Approve or reject an FDR action request.
# ADMIN and REVIEWER can make decisions.
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

    # Prevent an already-decided request from being decided again.
    if action.action_status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="This request has already been decided.",
        )

    # FIX 6: Prevent the request creator from approving or rejecting
    # their own request. Blocked attempts are audit-logged.
    enforce_maker_checker(
        db=db,
        maker_username=action.performed_by,
        current_user=current_user,
        entity_type="FDR_ACTION",
        entity_id=action.id,
        label="request",
    )

    fdr = db.get(FDR, action.fdr_id)

    if fdr is None:
        raise HTTPException(
            status_code=404,
            detail="FDR record not found.",
        )

    # Do not approve an action if the FDR has already been released.
    if (
        data.action_status == "APPROVED"
        and fdr.validity_status == "RELEASED"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "This FDR has already been released, so this request "
                "can no longer be approved."
            ),
        )

    # Update the FDR only when the request is approved.
    fdr_change = "No change to FDR status."

    if data.action_status == "APPROVED":
        fdr_change = apply_approved_action(
            fdr,
            action.action_type,
        )

    # Update the FDR action decision.
    action.action_status = data.action_status
    action.decided_by = current_user.username
    action.decided_at = datetime.utcnow()

    if data.remarks is not None:
        action.remarks = data.remarks

    # Record the decision and resulting FDR status changes.
    audit_entry = AuditLog(
        action=f"FDR_ACTION_{data.action_status}",
        entity_type="FDR_ACTION",
        entity_id=action.id,
        actor=current_user.username,
        details=(
            f"FDR ID: {action.fdr_id}; "
            f"Action type: {action.action_type}; "
            f"Status: {data.action_status}; "
            f"FDR change: {fdr_change}; "
            f"Remarks: {action.remarks or 'None'}"
        ),
    )

    db.add(audit_entry)

    # Save the FDR update, decision and audit entry together.
    try:
        db.commit()
        db.refresh(action)
    except Exception:
        db.rollback()
        raise

    return action_to_dict(action)