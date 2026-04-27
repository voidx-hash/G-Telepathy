"""
G Telepathy — Auth Router (Self-managed JWT + Cloudflare D1)

No Supabase. Passwords are hashed with bcrypt (passlib).
JWT tokens are signed with our own secret (python-jose).

Security notes:
- Passwords are never stored in plaintext — bcrypt with 12 rounds
- Generic error messages on login to prevent email enumeration
- Tokens expire in JWT_ACCESS_TOKEN_EXPIRE_MINUTES (default 60 min)
- get_current_user validates signature + expiry on every protected request
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import settings
from services.d1 import query, execute, D1Error, D1NotConfiguredError

logger = logging.getLogger(__name__)
router = APIRouter()
bearer = HTTPBearer()

# bcrypt password hashing — 12 rounds is a good production default
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


# ── JWT Helpers ────────────────────────────────────────────────────────────────
def _create_access_token(user_id: str, email: str, display_name: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": user_id,           # subject = user id
        "email": email,
        "display_name": display_name,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        raise AuthError(f"Invalid or expired token: {e}")


# ── Auth Dependency (used by all protected routes) ────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """
    Decode and validate the Bearer JWT. Returns the user payload dict.
    The payload includes: id, email, display_name
    """
    payload = _decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("Token is missing subject claim.")
    # Return a dict compatible with the rest of the codebase
    return {
        "id": user_id,
        "email": payload.get("email"),
        "user_metadata": {"display_name": payload.get("display_name")},
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(body: RegisterRequest):
    """
    Creates a new account. Stores hashed password in D1.
    Returns a JWT access token on success.
    """
    try:
        # Check if email already exists
        existing = await query(
            "SELECT id FROM users WHERE email = ?",
            [body.email.lower()],
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        user_id = str(uuid.uuid4())
        password_hash = pwd_context.hash(body.password)
        now = datetime.now(timezone.utc).isoformat()

        await execute(
            """
            INSERT INTO users (id, email, password_hash, display_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [user_id, body.email.lower(), password_hash, body.display_name, now, now],
        )

        access_token = _create_access_token(user_id, body.email.lower(), body.display_name)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
            "user": {
                "id": user_id,
                "email": body.email.lower(),
                "display_name": body.display_name,
            },
        }

    except HTTPException:
        raise
    except D1NotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is not configured. Set CLOUDFLARE_* environment variables.",
        )
    except D1Error as e:
        logger.error("D1 error during registration: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable. Please try again later.",
        )


@router.post("/login", summary="Sign in")
async def login(body: LoginRequest):
    """
    Verifies email + password. Returns a JWT on success.
    Deliberately uses a generic error to prevent email enumeration.
    """
    _GENERIC_AUTH_ERROR = "Invalid email or password."

    try:
        rows = await query(
            "SELECT id, email, password_hash, display_name FROM users WHERE email = ?",
            [body.email.lower()],
        )

        if not rows:
            # Still verify a dummy hash to prevent timing attacks
            pwd_context.dummy_verify()
            raise AuthError(_GENERIC_AUTH_ERROR)

        user = rows[0]
        if not pwd_context.verify(body.password, user["password_hash"]):
            raise AuthError(_GENERIC_AUTH_ERROR)

        # Update last_seen
        await execute(
            "UPDATE users SET last_seen = ? WHERE id = ?",
            [datetime.now(timezone.utc).isoformat(), user["id"]],
        )

        access_token = _create_access_token(user["id"], user["email"], user["display_name"])
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
        }

    except HTTPException:
        raise
    except D1NotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is not configured.",
        )
    except D1Error as e:
        logger.error("D1 error during login: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable.",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out",
)
async def logout(_user: dict = Depends(get_current_user)):
    """
    JWT is stateless — client must discard the token.
    For true revocation, add token_id to a D1 blocklist (future work).
    """
    return


@router.get("/me", summary="Get current user profile")
async def get_me(user: dict = Depends(get_current_user)):
    """Returns the authenticated user's profile from the JWT payload."""
    try:
        rows = await query(
            "SELECT id, email, display_name, avatar_url, bio, preferred_language, created_at FROM users WHERE id = ?",
            [user["id"]],
        )
        if rows:
            return rows[0]
        # Fallback to JWT payload if D1 is slow
        return {
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("user_metadata", {}).get("display_name"),
        }
    except D1NotConfiguredError:
        # Still works from JWT payload even without DB
        return {
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("user_metadata", {}).get("display_name"),
        }
    except D1Error:
        return {
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("user_metadata", {}).get("display_name"),
        }
