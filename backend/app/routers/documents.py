from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.document import FDRDocument
from app.models.fdr import FDR
from app.models.user import User
from app.services.document_integrity import check_document_integrity
from app.services.audit_service import add_audit_log
from app.services.document_service import (
    UPLOAD_DIR,
    save_document,
)

router = APIRouter(
    prefix="/api/fdrs",
    tags=["FDR Documents"],
)


# --------------------------------------------------
# 1. Upload FDR Document
# ADMIN and OFFICER only
# --------------------------------------------------
@router.post("/{fdr_id}/documents", status_code=201)
async def upload_fdr_document(
    fdr_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER")
    ),
):
    fdr = db.get(FDR, fdr_id)

    if fdr is None:
        raise HTTPException(
            status_code=404,
            detail="FDR not found.",
        )

    saved = await save_document(file)

    document = FDRDocument(
        fdr_id=fdr_id,
        original_filename=saved["original_filename"],
        stored_filename=saved["stored_filename"],
        content_type=saved["content_type"],
        sha256=saved["sha256"],
    )

    try:
        db.add(document)
        db.flush()

        add_audit_log(
            db=db,
            action="DOCUMENT_UPLOADED",
            entity_type="FDR_DOCUMENT",
            entity_id=document.id,
            actor=current_user.username,
            details=(
                f"Filename: {document.original_filename}; "
                f"FDR ID: {fdr_id}; "
                f"SHA-256: {saved['sha256']}"
            ),
        )
        db.commit()
        db.refresh(document)

    except Exception:
        db.rollback()
        saved["file_path"].unlink(missing_ok=True)
        raise

    return {
        "message": "Document uploaded successfully.",
        "document_id": document.id,
        "fdr_id": document.fdr_id,
        "filename": document.original_filename,
        "sha256": saved["sha256"],
    }


# --------------------------------------------------
# 2. List FDR Documents
# ADMIN, OFFICER, and REVIEWER only
# --------------------------------------------------
@router.get("/{fdr_id}/documents")
def list_fdr_documents(
    fdr_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER", "REVIEWER")
    ),
):
    fdr = db.get(FDR, fdr_id)

    if fdr is None:
        raise HTTPException(
            status_code=404,
            detail="FDR not found.",
        )

    documents = (
        db.query(FDRDocument)
        .filter(FDRDocument.fdr_id == fdr_id)
        .order_by(FDRDocument.uploaded_at.desc())
        .all()
    )

    return [
        {
            "id": doc.id,
            "fdr_id": doc.fdr_id,
            "filename": doc.original_filename,
            "content_type": doc.content_type,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in documents
    ]


# --------------------------------------------------
# 3. Download FDR Document
# ADMIN, OFFICER, and REVIEWER only
# --------------------------------------------------
@router.get("/{fdr_id}/documents/{document_id}")
def download_fdr_document(
    fdr_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER", "REVIEWER")
    ),
):
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

    integrity_status = check_document_integrity(
        db=db,
        document=document,
        current_user=current_user,
    )

    # Log only after the integrity check succeeds.
    add_audit_log(
        db=db,
        action="DOCUMENT_DOWNLOADED",
        entity_type="FDR_DOCUMENT",
        entity_id=document.id,
        actor=current_user.username,
        details=(
            f"Filename: {document.original_filename}; "
            f"FDR ID: {fdr_id}; "
            f"Integrity: {integrity_status}"
        ),
    )
    db.commit()


    file_path = UPLOAD_DIR / document.stored_filename

    return FileResponse(
        path=file_path,
        media_type=document.content_type,
        filename=Path(document.original_filename).name,
        content_disposition_type="attachment",
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Integrity-Status": integrity_status,
        },
    )
