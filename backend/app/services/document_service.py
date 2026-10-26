import hashlib
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


async def save_document(file: UploadFile) -> dict:
    content_type = file.content_type or ""

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPEG, and PNG files are allowed.",
        )

    original_filename = Path(file.filename or "document").name

    extension = Path(original_filename).suffix.lower()

    if extension != ALLOWED_TYPES[content_type]:
        raise HTTPException(
            status_code=400,
            detail="File extension does not match its content type.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB.",
        )

    # Basic file-signature validation.
    valid_signature = (
        content.startswith(b"%PDF-")
        if content_type == "application/pdf"
        else content.startswith(b"\xff\xd8\xff")
        if content_type == "image/jpeg"
        else content.startswith(b"\x89PNG\r\n\x1a\n")
    )

    if not valid_signature:
        raise HTTPException(
            status_code=400,
            detail="The file does not match the declared file type.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / stored_filename

    with file_path.open("xb") as output:
        output.write(content)

    return {
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "content_type": content_type,
        "file_path": file_path,
        "sha256": hashlib.sha256(content).hexdigest(),
    }