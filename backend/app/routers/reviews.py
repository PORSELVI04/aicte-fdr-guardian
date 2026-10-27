import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.audit_log import AuditLog
from app.models.document import FDRDocument
from app.models.fdr import FDR
from app.models.user import User
from app.models.verification import VerificationReview
from app.services.verification_service import run_ocr_verification

router = APIRouter(
    prefix="/api/reviews",
    tags=["Verification Reviews"]
)


class ReviewCreate(BaseModel):
    fdr_id: int = Field(gt=0)
    document_id: int = Field(gt=0)

class ReviewDecision(BaseModel):
    decision: str = Field(
        pattern="^(APPROVED|REJECTED|NEEDS_CORRECTION)$"
    )

    comments: str | None = Field(
        default=None,
        max_length=2000
    )


# 1. Create a review: ADMIN, OFFICER or REVIEWER
@router.post("/", status_code=201)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER", "REVIEWER")
    ),
):
    fdr = db.get(FDR, data.fdr_id)

    if fdr is None:
        raise HTTPException(status_code=404, detail="FDR not found.")

    document = (
        db.query(FDRDocument)
        .filter(
            FDRDocument.id == data.document_id,
            FDRDocument.fdr_id == data.fdr_id,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document does not belong to this FDR.",
        )

    # Calculate the verification result on the server.
    if document.content_type in {"image/jpeg", "image/png"}:
        result = run_ocr_verification(fdr, document)
        verification_status = result["verification_status"]
        discrepancy_details = result["issues"]
    else:
        verification_status = "REVIEW_REQUIRED"
        discrepancy_details = [
            "Automatic OCR is unavailable for this document type. "
            "Manual verification is required."
        ]

    review = VerificationReview(
        fdr_id=data.fdr_id,
        document_id=data.document_id,
        verification_status=verification_status,
        discrepancy_details=json.dumps(discrepancy_details),
    )

    db.add(review)
    db.flush()

    db.add(
        AuditLog(
            action="REVIEW_CREATED",
            entity_type="VERIFICATION_REVIEW",
            entity_id=review.id,
            actor=current_user.username,
            details=(
                f"Review created for FDR {data.fdr_id} "
                f"(server result: {verification_status})."
            ),
        )
    )

    db.commit()
    db.refresh(review)

    return {
        "review_id": review.id,
        "fdr_id": review.fdr_id,
        "document_id": review.document_id,
        "verification_status": review.verification_status,
        "reviewer_decision": review.reviewer_decision,
    }


# 2. List reviews: Any authenticated user
@router.get("/")
def list_reviews(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(VerificationReview)

    if status:
        allowed_statuses = {
            "PENDING",
            "APPROVED",
            "REJECTED",
            "NEEDS_CORRECTION",
        }

        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid review status."
            )

        query = query.filter(
            VerificationReview.reviewer_decision == status
        )

    reviews = query.order_by(
        VerificationReview.created_at.desc()
    ).all()

    return [
        {
            "review_id": review.id,
            "fdr_id": review.fdr_id,
            "document_id": review.document_id,
            "verification_status": review.verification_status,
            "discrepancy_details": (
                json.loads(review.discrepancy_details)
                if review.discrepancy_details
                else []
            ),
            "reviewer_decision": review.reviewer_decision,
            "reviewer_comments": review.reviewer_comments,
            "reviewed_by": review.reviewed_by,
            "created_at": review.created_at.isoformat(),
        }
        for review in reviews
    ]


# 3. Make a review decision: ADMIN or REVIEWER
@router.patch("/{review_id}/decision")
def decide_review(
    review_id: int,
    data: ReviewDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "REVIEWER")
    ),
):
    review = db.get(VerificationReview, review_id)

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Review not found."
        )

    if review.reviewer_decision != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="This review has already received a decision."
        )

    review.reviewer_decision = data.decision
    review.reviewer_comments = data.comments
    review.reviewed_at = datetime.now(timezone.utc)
    review.reviewed_by = current_user.username

    db.add(
        AuditLog(
            action="REVIEW_DECISION",
            entity_type="VERIFICATION_REVIEW",
            entity_id=review.id,
            actor=current_user.username,
            details=f"Decision: {data.decision}",
        )
    )

    db.commit()
    db.refresh(review)

    return {
        "review_id": review.id,
        "reviewer_decision": review.reviewer_decision,
        "reviewer_comments": review.reviewer_comments,
        "reviewed_by": review.reviewed_by,
        "reviewed_at": (
            review.reviewed_at.isoformat()
            if review.reviewed_at
            else None
        ),
    }