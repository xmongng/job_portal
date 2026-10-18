"""Private PDF storage. No static mount, client filenames or public file URLs."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from app.core.config import get_settings


def storage_file(key: str) -> Path:
    root = get_settings().file_storage_path.resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root) or path == root:
        raise HTTPException(404, "File not found")
    return path


def save_pdf(upload: UploadFile) -> tuple[str, int]:
    settings = get_settings()
    if upload.content_type != "application/pdf" or not (upload.filename or "").lower().endswith(
        ".pdf"
    ):
        raise HTTPException(422, "Only PDF files are accepted")
    data = upload.file.read(settings.max_resume_bytes + 1)
    if len(data) > settings.max_resume_bytes:
        raise HTTPException(413, "PDF must not exceed 5 MiB")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(422, "Invalid PDF signature")
    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted or len(reader.pages) == 0:
            raise ValueError("Encrypted or empty PDF")
    except Exception as exc:
        raise HTTPException(422, "Invalid, encrypted or empty PDF") from exc
    key = f"resumes/{uuid4().hex}.pdf"
    target = storage_file(key)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as out:
        out.write(data)
    return key, len(data)
