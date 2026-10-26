import pytesseract
from pathlib import Path

from app.dependencies import get_current_user, require_roles
from app.models.user import User

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import FDRDocument
from app.models.fdr import FDR
from app.services.document_service import UPLOAD_DIR
from app.services.ocr_service import (
    compare_text,
    extract_fdr_fields,
    extract_text_from_image,
)

router = APIRouter(
    prefix="/api/fdrs",
    tags=["OCR Verification"],
)


@router.post("/{fdr_id}/documents/{document_id}/verify")
def verify_fdr_document(
    fdr_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "OFFICER", "REVIEWER")),
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

    if document.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(
            status_code=400,
            detail="OCR currently supports JPEG and PNG images only.",
        )

    file_path = UPLOAD_DIR / document.stored_filename

    try:
        text = extract_text_from_image(str(file_path))
    except pytesseract.pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Tesseract OCR is not installed or its path is incorrect.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Could not process the image: {type(exc).__name__}",
        )

    fields = extract_fdr_fields(text)

    fdr_number_comparison = compare_text(
        fields["fdr_number"],
        fdr.fdr_number,
    )

    amount_comparison = compare_text(
        fields["deposit_amount"],
        str(fdr.deposit_amount),
    )

    issues = []

    if fdr_number_comparison["status"] != "MATCH":
        issues.append("FDR number needs manual review.")

    if amount_comparison["status"] != "MATCH":
        issues.append("Deposit amount needs manual review.")

    return {
        "fdr_id": fdr.id,
        "document_id": document.id,
        "extracted_fields": fields,
        "comparison": {
            "fdr_number": fdr_number_comparison,
            "deposit_amount": amount_comparison,
        },
        "issues": issues,
        "verification_status": (
            "REVIEW_REQUIRED" if issues else "OCR_MATCHED"
        ),
        "important_note": (
            "OCR matching does not establish certificate authenticity. "
            "Authorized bank verification and human review are required."
        ),
    }