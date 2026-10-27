import pytesseract

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.document import FDRDocument
from app.models.fdr import FDR
from app.models.user import User
from app.services.document_service import UPLOAD_DIR
from app.services.ocr_service import (
    compare_amount,
    compare_identifier,
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
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER", "REVIEWER")
    ),
):
    # 1. Find the FDR record.
    fdr = db.get(FDR, fdr_id)

    if fdr is None:
        raise HTTPException(
            status_code=404,
            detail="FDR record not found.",
        )

    # 2. Ensure the document belongs to this FDR.
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

    # 3. Check the supported image type.
    if document.content_type not in {
        "image/jpeg",
        "image/png",
    }:
        raise HTTPException(
            status_code=400,
            detail="OCR currently supports JPEG and PNG images only.",
        )

    # 4. Run OCR on the stored document.
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

    # 5. Extract the fields from the OCR text.
    fields = extract_fdr_fields(text)

    # 6. Compare the FDR number exactly.
    fdr_number_comparison = compare_identifier(
        fields["fdr_number"],
        fdr.fdr_number,
    )

    # 7. Compare the deposit amount numerically and exactly.
    amount_comparison = compare_amount(
        fields["deposit_amount"],
        str(fdr.deposit_amount),
    )

    # 8. Collect all issues that require manual review.
    issues = []

    if fdr_number_comparison["status"] != "MATCH":
        issues.append("FDR number needs manual review.")

    if amount_comparison["status"] != "MATCH":
        issues.append("Deposit amount needs manual review.")

    # 9. Calculate the status on the server.
    verification_status = (
        "REVIEW_REQUIRED" if issues else "OCR_MATCHED"
    )

    # 10. Return the server-generated result.
    return {
        "fdr_id": fdr.id,
        "document_id": document.id,
        "extracted_fields": fields,
        "comparison": {
            "fdr_number": fdr_number_comparison,
            "deposit_amount": amount_comparison,
        },
        "issues": issues,
        "verification_status": verification_status,
        "important_note": (
            "OCR matching does not establish certificate authenticity. "
            "Authorized bank verification and human review are required."
        ),
    }