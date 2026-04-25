"""G Telepathy — Google Cloud Translate Service"""
import httpx
from config import settings


class TranslationService:
    """Handles text translation via Google Cloud Translate API v2."""

    BASE_URL = "https://translation.googleapis.com/language/translate/v2"

    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str | None = None,
    ) -> dict:
        params = {
            "q": text,
            "target": target_language,
            "key": settings.google_translate_api_key,
            "format": "text",
        }
        if source_language:
            params["source"] = source_language

        async with httpx.AsyncClient() as client:
            response = await client.post(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        translation = data["data"]["translations"][0]
        return {
            "translated_text": translation["translatedText"],
            "detected_source_language": translation.get("detectedSourceLanguage", source_language or "unknown"),
            "target_language": target_language,
        }

    async def detect_language(self, text: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/detect",
                params={"q": text, "key": settings.google_translate_api_key},
            )
            response.raise_for_status()
            data = response.json()

        detection = data["data"]["detections"][0][0]
        return {
            "language": detection["language"],
            "confidence": detection["confidence"],
        }

    async def get_supported_languages(self, target: str = "en") -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/languages",
                params={"target": target, "key": settings.google_translate_api_key},
            )
            response.raise_for_status()
            data = response.json()

        return data["data"]["languages"]
