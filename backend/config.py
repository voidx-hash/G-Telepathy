"""
G Telepathy — Application Configuration
Raises at startup if required secrets are missing.
"""
import os
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from typing import List


class Settings(BaseSettings):
    # ── Supabase ────────────────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # ── Google Cloud ─────────────────────────────────────────────────────────
    google_cloud_project_id: str = ""
    google_translate_api_key: str = ""
    google_speech_api_key: str = ""

    # ── ElevenLabs (Voice Cloning) ───────────────────────────────────────────
    elevenlabs_api_key: str = ""

    # ── JWT ──────────────────────────────────────────────────────────────────
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60  # 1 hour, not 24h

    # ── App ──────────────────────────────────────────────────────────────────
    backend_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]
    environment: str = "development"

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        allowed = {"HS256", "HS384", "HS512"}
        if v not in allowed:
            raise ValueError(f"jwt_algorithm must be one of {allowed}")
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors(cls, v) -> List[str]:
        if isinstance(v, str):
            v = [o.strip() for o in v.split(",")]
        # In production, never allow wildcard origins
        for origin in v:
            if origin == "*":
                raise ValueError("Wildcard CORS origin '*' is not allowed for security reasons.")
        return v

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        # In production, all secrets must be set
        if self.environment == "production":
            required = {
                "supabase_url": self.supabase_url,
                "supabase_anon_key": self.supabase_anon_key,
                "supabase_service_role_key": self.supabase_service_role_key,
                "jwt_secret_key": self.jwt_secret_key,
            }
            missing = [k for k, v in required.items() if not v]
            if missing:
                raise ValueError(f"Missing required environment variables for production: {missing}")

        # Always require a non-default JWT secret
        if not self.jwt_secret_key:
            # In dev, auto-generate a temporary secret and warn
            self.jwt_secret_key = secrets.token_hex(32)
            print(
                "[WARNING] jwt_secret_key is not set. A random temporary key has been generated. "
                "This means all sessions will be invalidated on restart. "
                "Set JWT_SECRET_KEY in your .env file."
            )
        elif self.jwt_secret_key in ("change-me-in-production", "secret", "password", "12345"):
            raise ValueError(
                "jwt_secret_key is set to an insecure default value. "
                "Please set a strong random secret in your .env file."
            )
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
