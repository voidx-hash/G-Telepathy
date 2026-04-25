"""
G Telepathy — Google Cloud Translate Service

Security notes:
- API key is sent via JSON body (not URL params) to avoid access log exposure
- Custom exception types so callers can distinguish API errors from config errors
- Timeouts on all HTTP calls to prevent hanging
"""
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)


class TranslationNotConfiguredError(Exception):
    """Raised when the Google Translate API key is missing."""


class TranslationServiceError(Exception):
    """Raised when the Google Translate API returns a non-success response."""


class TranslationService:
    """Handles text translation via Google Cloud Translate API v2."""

    # Using POST so the API key is in the body, not the URL
    BASE_URL = "https://translation.googleapis.com/language/translate/v2"
    TIMEOUT = httpx.Timeout(10.0, connect=5.0)

    def _require_api_key(self) -> str:
        key = settings.google_translate_api_key
        if not key:
            raise TranslationNotConfiguredError(
                "GOOGLE_TRANSLATE_API_KEY is not set."
            )
        return key

    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str | None = None,
    ) -> dict:
        """
        Translates `text` to `target_language`.
        If `source_language` is None, Google auto-detects it.
        """
        api_key = self._require_api_key()

        payload: dict = {
            "q": text,
            "target": target_language,
            "format": "text",
            "key": api_key,
        }
        if source_language:
            payload["source"] = source_language

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                # POST with JSON body keeps key out of server access logs
                response = await client.post(self.BASE_URL, params={"key": api_key}, json={
                    "q": text,
                    "target": target_language,
                    "format": "text",
                    **({"source": source_language} if source_language else {}),
                })
        except httpx.TimeoutException:
            raise TranslationServiceError("Translation request timed out.")
        except httpx.RequestError as e:
            raise TranslationServiceError(f"Network error reaching translation API: {type(e).__name__}")

        if response.status_code != 200:
            logger.warning(
                "Google Translate API error %d: %s",
                response.status_code,
                response.text[:200],  # log only first 200 chars
            )
            raise TranslationServiceError(
                f"Translation API returned status {response.status_code}."
            )

        try:
            data = response.json()
            translation = data["data"]["translations"][0]
        except (KeyError, IndexError, ValueError) as e:
            raise TranslationServiceError(f"Unexpected response format from translation API: {e}")

        return {
            "translated_text": translation["translatedText"],
            "detected_source_language": translation.get(
                "detectedSourceLanguage", source_language or "unknown"
            ),
            "target_language": target_language,
        }

    async def detect_language(self, text: str) -> dict:
        """Detects the language of the given text."""
        api_key = self._require_api_key()

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(
                    f"{self.BASE_URL}/detect",
                    params={"key": api_key},
                    json={"q": text},
                )
        except httpx.TimeoutException:
            raise TranslationServiceError("Language detection request timed out.")
        except httpx.RequestError as e:
            raise TranslationServiceError(f"Network error: {type(e).__name__}")

        if response.status_code != 200:
            raise TranslationServiceError(
                f"Language detection API returned status {response.status_code}."
            )

        try:
            data = response.json()
            detection = data["data"]["detections"][0][0]
        except (KeyError, IndexError, ValueError) as e:
            raise TranslationServiceError(f"Unexpected response format: {e}")

        return {
            "language": detection["language"],
            "confidence": detection["confidence"],
        }

    async def get_supported_languages(self, target: str = "en") -> list:
        """Returns all languages supported by Google Translate."""
        api_key = self._require_api_key()

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(
                    f"{self.BASE_URL}/languages",
                    params={"target": target, "key": api_key},
                )
        except httpx.TimeoutException:
            raise TranslationServiceError("Language list request timed out.")
        except httpx.RequestError as e:
            raise TranslationServiceError(f"Network error: {type(e).__name__}")

        if response.status_code != 200:
            raise TranslationServiceError(
                f"Languages API returned status {response.status_code}."
            )

        try:
            data = response.json()
            return data["data"]["languages"]
        except (KeyError, ValueError) as e:
            raise TranslationServiceError(f"Unexpected response format: {e}")
