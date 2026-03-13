import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.config import settings
from app.models.user import User
from app.core.dependencies import require_auth

router = APIRouter(prefix="/api/upload", tags=["Upload"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...), current_user: User = Depends(require_auth)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Faqat rasm fayllar ruxsat etilgan: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, "Fayl hajmi 5MB dan oshmasligi kerak")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    return {"filename": filename, "path": f"/api/uploads/{filename}"}
