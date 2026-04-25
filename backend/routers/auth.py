"""
G Telepathy — Auth Router
Uses Supabase Auth. No passwords are stored in our DB.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
import httpx
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
bearer = HTTPBearer()

SUPABASE_AUTH_URL = f"{settings.supabase_url}/auth/v1"


# ── Schemas ────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @field_validator("display_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 60:
            raise ValueError("Display name must be between 2 and 60 characters.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Helpers ────────────────────────────────────────────────────────────────────
def _supabase_headers() -> dict:
    """Build Supabase REST API headers (service role never exposed to clients)."""
    return {
        "apikey": settings.supabase_anon_key,
        "Content-Type": "application/json",
    }


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    """Validate the Bearer token with Supabase and return the user payload."""
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        )
    token = credentials.credentials
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{SUPABASE_AUTH_URL}/user",
                headers={**_supabase_headers(), "Authorization": f"Bearer {token}"},
            )
        if resp.status_code == 401:
            raise AuthError("Invalid or expired token.")
        resp.raise_for_status()
        return resp.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the authentication service.",
        )


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(body: RegisterRequest):
    """
    Creates a new account via Supabase Auth.
    Returns access + refresh tokens on success.
    Requires Supabase to be configured.
    """
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.",
        )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{SUPABASE_AUTH_URL}/signup",
                headers=_supabase_headers(),
                json={
                    "email": body.email,
                    "password": body.password,
                    "data": {"display_name": body.display_name},
                },
            )
        if resp.status_code == 400:
            detail = resp.json().get("msg", "Registration failed.")
            # Normalise Supabase error messages — don't expose internal details
            if "already registered" in detail.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists.",
                )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid registration data.")
        resp.raise_for_status()
        data = resp.json()
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "token_type": "bearer",
            "user": {
                "id": data.get("user", {}).get("id"),
                "email": data.get("user", {}).get("email"),
                "display_name": body.display_name,
            },
        }
    except HTTPException:
        raise
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the authentication service.",
        )


@router.post("/login", summary="Sign in with email and password")
async def login(body: LoginRequest):
    """
    Authenticates a user with Supabase Auth.
    Returns access + refresh tokens.
    Uses a generic error message to prevent user enumeration.
    """
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{SUPABASE_AUTH_URL}/token?grant_type=password",
                headers=_supabase_headers(),
                json={"email": body.email, "password": body.password},
            )
        if resp.status_code in (400, 401, 422):
            # Generic message to prevent email enumeration attacks
            raise AuthError("Invalid email or password.")
        resp.raise_for_status()
        data = resp.json()
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "token_type": "bearer",
            "expires_in": data.get("expires_in"),
        }
    except HTTPException:
        raise
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the authentication service.",
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Sign out")
async def logout(user: dict = Depends(get_current_user), credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Invalidates the user's session token in Supabase."""
    if not settings.supabase_url:
        return
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.post(
                f"{SUPABASE_AUTH_URL}/logout",
                headers={
                    **_supabase_headers(),
                    "Authorization": f"Bearer {credentials.credentials}",
                },
            )
    except Exception:
        logger.warning("Logout request to Supabase failed, continuing silently.")


@router.get("/me", summary="Get current user profile")
async def get_me(user: dict = Depends(get_current_user)):
    """Returns the authenticated user's profile. Requires a valid Bearer token."""
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "display_name": user.get("user_metadata", {}).get("display_name"),
        "created_at": user.get("created_at"),
    }
