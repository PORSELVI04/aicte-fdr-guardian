from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.document import FDRDocument
from app.models.fdr import FDR
from app.models.user import User
from app.services.verification_service import run_ocr_verification


router = APIRouter(
    prefix="/api/fdrs",
    tags=["OCR Verification"],
)


@router.post("/{fdr_id}/documents/{document_id}/verify")
def verify_fdr_document(
    fdr_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER", "REVIEWER")
    ),
):
    fdr = db.get(FDR, fdr_id)

    if fdr is None:
        raise HTTPException(
            status_code=404,
            detail="FDR record not found.",
        )

    document = (
        db.query(FDRDocument)
        .filter(
            FDRDocument.id == document_id,
            FDRDocument.fdr_id == fdr_id,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found for this FDR.",
        )

    return run_ocr_verification(fdr, document)
