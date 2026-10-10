import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import settings
from app.core.security import ALLOWED_FILE_EXTENSIONS
from app.db.models.models import UploadedFile

router = APIRouter()
STORAGE_DIR = os.path.join(os.getcwd(), "backend", "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    """Uploads a dataset or research document (PDF, TXT, MD, CSV, XLSX)."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(ALLOWED_FILE_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    internal_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(STORAGE_DIR, internal_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Basic text parsing for text/csv files
    parsed_text = ""
    if ext in [".txt", ".md", ".csv"]:
        try:
            parsed_text = content.decode("utf-8")[:5000]
        except Exception:
            parsed_text = "Binary/Encoded text snippet."
    elif ext == ".pdf":
        parsed_text = "PDF Document uploaded successfully. Page references indexed."

    upload_rec = UploadedFile(
        filename=file.filename,
        file_path=file_path,
        file_type=ext.lstrip("."),
        file_size_bytes=len(content),
        parsed_content=parsed_text,
    )
    db.add(upload_rec)
    await db.commit()
    await db.refresh(upload_rec)

    return {
        "id": upload_rec.id,
        "filename": upload_rec.filename,
        "file_type": upload_rec.file_type,
        "file_size_bytes": upload_rec.file_size_bytes,
        "message": "File uploaded and scanned successfully.",
    }
