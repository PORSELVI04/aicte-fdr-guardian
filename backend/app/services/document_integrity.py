import hashlib
import hmac
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.document import FDRDocument
from app.models.user import User
from app.services.document_service import UPLOAD_DIR


def calculate_sha256(file_path: Path) -> str:
    """Calculate a file's SHA-256 hash in 1 MiB chunks."""
    digest = hashlib.sha256()

    with file_path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def check_document_integrity(
    db: Session,
    document: FDRDocument,
    current_user: User,
) -> str:
    """Verify a document against its recorded hash."""
    file_path = UPLOAD_DIR / document.stored_filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored document file not found.",
        )

    # Backward compatibility for documents uploaded before Fix 7.
    if not document.sha256:
        return "NOT_RECORDED"

    actual_hash = calculate_sha256(file_path)
    expected_hash = document.sha256

    if hmac.compare_digest(expected_hash, actual_hash):
        return "VERIFIED"

    db.add(
        AuditLog(
            action="DOCUMENT_INTEGRITY_FAILED",
            entity_type="FDR_DOCUMENT",
            entity_id=document.id,
            actor=current_user.username,
            details=(
                f"SHA-256 mismatch for document {document.id}. "
                f"Expected prefix: {expected_hash[:12]}; "
                f"actual prefix: {actual_hash[:12]}."
            ),
        )
    )
    db.commit()

    raise HTTPException(
        status_code=409,
        detail="Document integrity verification failed. "
               "The stored file may have been modified.",
    )
