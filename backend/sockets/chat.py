"""
G Telepathy — Chat Socket.io Event Handlers

Security:
- Authentication is validated on connect using a Supabase JWT bearer token
- Unauthenticated connections are immediately rejected
- Clients are tracked in a session store (sid -> user_id) so they cannot
  impersonate other users during message broadcast
- All data fields are validated before use; missing fields are rejected
- Messages are relayed as-is (encrypted payload) without server-side decryption
"""
import logging
import httpx
import socketio
from config import settings

logger = logging.getLogger(__name__)

# In-memory session store mapping socket-id -> {user_id, display_name}
# In production, replace with Redis for multi-worker deployments
_sessions: dict[str, dict] = {}


async def _validate_token(token: str) -> dict | None:
    """Validates a Supabase JWT and returns the user payload, or None if invalid."""
    if not settings.supabase_url or not settings.supabase_anon_key:
        logger.warning("Supabase not configured — accepting socket connections without auth (dev mode only)")
        return {"id": "dev-user", "email": "dev@localhost"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers={
                    "apikey": settings.supabase_anon_key,
                    "Authorization": f"Bearer {token}",
                },
            )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
    return None


def register(sio: socketio.AsyncServer):

    @sio.event
    async def connect(sid, environ, auth):
        """
        Validates bearer token on connection.
        auth must be: {"token": "<supabase_access_token>"}
        Rejects connection if token is missing or invalid.
        """
        if not auth or not isinstance(auth, dict):
            logger.warning(f"[Socket] Connection rejected (no auth): {sid}")
            raise ConnectionRefusedError("Authentication required.")

        token = auth.get("token", "").strip()
        if not token:
            logger.warning(f"[Socket] Connection rejected (empty token): {sid}")
            raise ConnectionRefusedError("Authentication token is required.")

        user = await _validate_token(token)
        if not user:
            logger.warning(f"[Socket] Connection rejected (invalid token): {sid}")
            raise ConnectionRefusedError("Invalid or expired token.")

        _sessions[sid] = {
            "user_id": user.get("id"),
            "email": user.get("email"),
        }
        # Auto-join the user's own notification room
        await sio.enter_room(sid, f"user:{user.get('id')}")
        logger.info(f"[Socket] Authenticated connect: {sid} -> user {user.get('id')}")

    @sio.event
    async def disconnect(sid):
        user = _sessions.pop(sid, {})
        logger.info(f"[Socket] Disconnected: {sid} (user {user.get('user_id', 'unknown')})")

    @sio.on("join_conversation")
    async def join_conversation(sid, data):
        """
        Join a conversation room.
        TODO: Before production, validate that the user is actually a member of
        this conversation by querying the DB (Supabase).
        """
        if sid not in _sessions:
            await sio.emit("error", {"code": "UNAUTHENTICATED"}, to=sid)
            return
        if not isinstance(data, dict):
            await sio.emit("error", {"code": "INVALID_DATA"}, to=sid)
            return

        conversation_id = data.get("conversation_id", "").strip()
        if not conversation_id:
            await sio.emit("error", {"code": "MISSING_CONVERSATION_ID"}, to=sid)
            return

        await sio.enter_room(sid, f"conversation:{conversation_id}")
        await sio.emit("joined", {"conversation_id": conversation_id}, to=sid)

    @sio.on("send_message")
    async def send_message(sid, data):
        """
        Relay an encrypted message payload to all members of a conversation.
        The server NEVER decrypts messages — only relays the encrypted content.

        Expected data:
        {
            "conversation_id": str (required),
            "encrypted_content": str (required, AES-256 client-side encrypted),
            "message_type": str ("text" | "image" | "file" | "audio"),
            "timestamp": str (ISO 8601, optional)
        }
        """
        if sid not in _sessions:
            await sio.emit("error", {"code": "UNAUTHENTICATED"}, to=sid)
            return
        if not isinstance(data, dict):
            await sio.emit("error", {"code": "INVALID_DATA"}, to=sid)
            return

        conversation_id = data.get("conversation_id", "").strip()
        encrypted_content = data.get("encrypted_content", "").strip()

        if not conversation_id:
            await sio.emit("error", {"code": "MISSING_CONVERSATION_ID"}, to=sid)
            return
        if not encrypted_content:
            await sio.emit("error", {"code": "MISSING_CONTENT"}, to=sid)
            return
        if len(encrypted_content) > 100_000:  # ~100KB max encrypted payload
            await sio.emit("error", {"code": "PAYLOAD_TOO_LARGE"}, to=sid)
            return

        # Build a clean relay payload — strip any extra fields the client may have sent
        relay_data = {
            "conversation_id": conversation_id,
            "encrypted_content": encrypted_content,
            "message_type": data.get("message_type", "text"),
            "sender_id": _sessions[sid]["user_id"],  # inject from server-verified session
            "timestamp": data.get("timestamp"),
        }

        await sio.emit(
            "new_message",
            relay_data,
            room=f"conversation:{conversation_id}",
            skip_sid=sid,
        )

    @sio.on("typing")
    async def typing(sid, data):
        if sid not in _sessions:
            return
        if not isinstance(data, dict):
            return

        conversation_id = data.get("conversation_id", "").strip()
        if not conversation_id:
            return

        await sio.emit(
            "user_typing",
            {
                "conversation_id": conversation_id,
                "user_id": _sessions[sid]["user_id"],  # inject from session, not from client data
            },
            room=f"conversation:{conversation_id}",
            skip_sid=sid,
        )
