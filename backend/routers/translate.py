"""
G Telepathy — Translation Router (Google Cloud Translate API)

Security notes:
- API key is sent via Authorization header to avoid URL logging exposure
- Text input is length-limited to prevent abuse
- Generic error messages prevent internal detail leakage
- Endpoint requires a valid user session (auth dependency)
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, field_validator
from routers.auth import get_current_user
from services.translation import TranslationService, TranslationServiceError, TranslationNotConfiguredError

logger = logging.getLogger(__name__)
router = APIRouter()
translation_service = TranslationService()

_MAX_TEXT_LEN = 5000  # Google Translate API hard limit is 5000 chars per request


# ── Schemas ────────────────────────────────────────────────────────────────────
class TranslateRequest(BaseModel):
    text: str
    target_language: str
    source_language: str | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Text cannot be empty.")
        if len(v) > _MAX_TEXT_LEN:
            raise ValueError(f"Text exceeds maximum length of {_MAX_TEXT_LEN} characters.")
        return v

    @field_validator("target_language")
    @classmethod
    def validate_target_language(cls, v: str) -> str:
        v = v.strip().lower()
        if not v or len(v) > 10:
            raise ValueError("Invalid target language code.")
        # Basic BCP-47 language code format check (e.g. 'en', 'zh-CN')
        if not all(c.isalpha() or c == "-" for c in v):
            raise ValueError("Language code must only contain letters and hyphens.")
        return v


class TranslateResponse(BaseModel):
    translated_text: str
    detected_source_language: str
    target_language: str


class DetectRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Text cannot be empty.")
        if len(v) > 500:
            raise ValueError("Text for detection exceeds 500 characters.")
        return v


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.post(
    "/text",
    response_model=TranslateResponse,
    summary="Translate text",
    description="Translates text to the target language. Requires authentication.",
)
async def translate_text(
    request: TranslateRequest,
    _user: dict = Depends(get_current_user),
):
    """
    Translates the provided text using Google Cloud Translate API.
    Authentication required to prevent abuse.
    """
    try:
        result = await translation_service.translate(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language,
        )
        return result
    except TranslationNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service is not configured. Set GOOGLE_TRANSLATE_API_KEY.",
        )
    except TranslationServiceError as e:
        logger.warning(f"Translation API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Translation service returned an error. Please try again.",
        )
    except Exception:
        logger.exception("Unexpected error in translate_text")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get(
    "/languages",
    summary="Get supported languages",
    description="Returns all languages supported by Google Translate. Requires authentication.",
)
async def get_supported_languages(
    target: str = "en",
    _user: dict = Depends(get_current_user),
):
    if not all(c.isalpha() or c == "-" for c in target) or len(target) > 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid target language code.")
    try:
        languages = await translation_service.get_supported_languages(target)
        return {"languages": languages}
    except TranslationNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service is not configured.",
        )
    except TranslationServiceError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch languages from translation service.",
        )


@router.post(
    "/detect",
    summary="Detect language",
    description="Detects the language of the provided text. Requires authentication.",
)
async def detect_language(
    body: DetectRequest,
    _user: dict = Depends(get_current_user),
):
    """Changed from GET query param to POST body to prevent text being logged in server access logs."""
    try:
        result = await translation_service.detect_language(body.text)
        return result
    except TranslationNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service is not configured.",
        )
    except TranslationServiceError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Language detection failed. Please try again.",
        )
