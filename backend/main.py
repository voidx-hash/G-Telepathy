"""
G Telepathy — FastAPI Application Entry Point
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import socketio
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Socket.io ─────────────────────────────────────────────────────────────────
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_origins,
    logger=False,
    engineio_logger=False,
)

# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="G Telepathy API",
    description="Backend for the G Telepathy secure communication platform",
    version="1.0.0",
    # Disable OpenAPI docs in production to avoid leaking API structure
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # explicit, not "*"
    allow_headers=["Authorization", "Content-Type", "Accept"],  # explicit, not "*"
)

# ── Security Headers Middleware ────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Remove server info leakage — MutableHeaders has no .pop(), use del
    if "server" in response.headers:
        del response.headers["server"]
    return response

# ── Global Error Handlers (never leak stack traces) ───────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Sanitize errors: strip 'url' and non-serializable 'ctx' values
    def _clean_error(e: dict) -> dict:
        clean = {k: v for k, v in e.items() if k not in ("url",)}
        if "ctx" in clean:
            clean["ctx"] = {k: str(v) for k, v in clean["ctx"].items()}
        return clean
    errors = [_clean_error(e) for e in exc.errors()]
    logger.warning(f"Validation error on {request.url}: {errors}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request data", "errors": errors},
    )

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

# ── Routers ────────────────────────────────────────────────────────────────────
from routers import auth, chat, calls, rooms, translate

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(calls.router, prefix="/api/calls", tags=["Calls"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["Rooms"])
app.include_router(translate.router, prefix="/api/translate", tags=["Translation"])

# ── Socket.io Events ───────────────────────────────────────────────────────────
from sockets import chat as chat_sockets, calls as call_sockets

chat_sockets.register(sio)
call_sockets.register(sio)

# ── ASGI Mount ─────────────────────────────────────────────────────────────────
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "G Telepathy API",
        "version": "1.0.0",
        "phase": "beta",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
