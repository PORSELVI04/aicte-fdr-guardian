from fastapi import HTTPException
import pytesseract

from app.models.document import FDRDocument
from app.models.fdr import FDR
from app.services.document_service import UPLOAD_DIR
from app.services.ocr_service import (
    compare_amount,
    compare_identifier,
    extract_fdr_fields,
    extract_text_from_image,
)


SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png"}


def run_ocr_verification(fdr: FDR, document: FDRDocument) -> dict:
    """Calculate the document verification result on the server."""

    if document.content_type not in SUPPORTED_IMAGE_TYPES:
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

    fdr_number_comparison = compare_identifier(
        fields["fdr_number"],
        fdr.fdr_number,
    )

    amount_comparison = compare_amount(
        fields["deposit_amount"],
        str(fdr.deposit_amount),
    )

    issues = []

    if fdr_number_comparison["status"] != "MATCH":
        issues.append("FDR number needs manual review.")

    if amount_comparison["status"] != "MATCH":
        issues.append("Deposit amount needs manual review.")

    verification_status = (
        "REVIEW_REQUIRED" if issues else "OCR_MATCHED"
    )

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
