"""G Telepathy — Translation Router (Google Cloud Translate API)"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.translation import TranslationService

router = APIRouter()
translation_service = TranslationService()


class TranslateRequest(BaseModel):
    text: str
    target_language: str
    source_language: str | None = None  # Auto-detect if None


class TranslateResponse(BaseModel):
    translated_text: str
    detected_source_language: str
    target_language: str


@router.post("/text", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate a text message to the target language."""
    try:
        result = await translation_service.translate(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages(target: str = "en"):
    """Get all languages supported by Google Translate."""
    try:
        languages = await translation_service.get_supported_languages(target)
        return {"languages": languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect")
async def detect_language(text: str):
    """Detect the language of a given text."""
    try:
        result = await translation_service.detect_language(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
