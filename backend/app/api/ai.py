import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from google.genai import errors as genai_errors

from app.database import get_db
from app.core.dependencies import require_auth
from app.models.user import User
from app.config import settings
from app.services import ai_service

router = APIRouter(prefix="/api/ai", tags=["AI"])
logger = logging.getLogger(__name__)


def _check_api_key():
    if not settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY_2 and not settings.GEMINI_API_KEY_3:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY sozlanmagan. .env faylga GEMINI_API_KEY qo'shing.")


def _handle_ai_error(e: Exception):
    """Gemini API xatolarini foydalanuvchiga tushunarli qilish."""
    # google-genai SDK xato turlari
    if isinstance(e, genai_errors.ClientError):
        status = getattr(e, 'status', 0) or 0
        if status == 403 or "PERMISSION_DENIED" in str(e):
            raise HTTPException(status_code=401, detail="Gemini API kaliti noto'g'ri yoki bloklangan. .env faylni tekshiring.")
        if status == 429 or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(status_code=429, detail="Gemini API so'rovlar limiti oshdi. Biroz kutib qayta urinib ko'ring.")
    if isinstance(e, genai_errors.ServerError):
        raise HTTPException(status_code=502, detail="Gemini API serveri vaqtincha ishlamayapti. Keyinroq urinib ko'ring.")

    msg = str(e)
    logger.error(f"AI xatolik: {e}")
    raise HTTPException(status_code=500, detail=f"AI xizmati xatosi: {msg[:200]}")


class SuggestCategoryRequest(BaseModel):
    name: str
    description: str | None = None


class ChatRequest(BaseModel):
    message: str


class AutoFillRequest(BaseModel):
    name: str


@router.post("/suggest-category")
def suggest_category(
    req: SuggestCategoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """Aktiv nomi asosida avtomatik kategoriya tavsiya qilish."""
    _check_api_key()
    try:
        return ai_service.suggest_category(db, req.name, req.description)
    except HTTPException:
        raise
    except Exception as e:
        _handle_ai_error(e)


@router.get("/risk-assessment")
def risk_assessment(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """Aktivlardan foydalanish tarixiga qarab nosozlik xavfini bashorat qilish."""
    _check_api_key()
    try:
        return ai_service.get_risk_assessment(db)
    except HTTPException:
        raise
    except Exception as e:
        _handle_ai_error(e)


@router.get("/insights")
def insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """Inventarizatsiya va audit uchun AI asosidagi tavsiyalar."""
    _check_api_key()
    try:
        return ai_service.get_insights(db)
    except HTTPException:
        raise
    except Exception as e:
        _handle_ai_error(e)


@router.get("/problematic-assets")
def problematic_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """Izohlarni tahlil qilish orqali muammoli aktivlarni aniqlash."""
    _check_api_key()
    try:
        return ai_service.get_problematic_assets(db)
    except HTTPException:
        raise
    except Exception as e:
        _handle_ai_error(e)


@router.post("/chat")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """AI chatbot — tabiiy tilda savol-javob."""
    _check_api_key()
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Savol bo'sh bo'lishi mumkin emas")
    try:
        return ai_service.chat_with_ai(db, req.message.strip())
    except HTTPException:
        raise
    except Exception as e:
        _handle_ai_error(e)


@router.post("/auto-fill")
def auto_fill(
    req: AutoFillRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """Aktiv nomi asosida barcha maydonlarni AI orqali to'ldirish."""
    _check_api_key()
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Aktiv nomi bo'sh bo'lishi mumkin emas")
    try:
        return ai_service.auto_fill_asset(db, req.name.strip())
    except HTTPException:
        raise
    except Exception as e:
        _handle_ai_error(e)


