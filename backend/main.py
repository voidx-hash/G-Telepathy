"""
G Telepathy — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from config import settings

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
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"status": "ok", "service": "G Telepathy API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
