"""
G Telepathy — Chat Router

Security:
- All endpoints require a valid Bearer token
- conversation_id path validated to prevent path traversal
- Messages stored encrypted (client must send encrypted payload)
- GET messages requires membership check (TODO: enforce in DB)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam
from pydantic import BaseModel, field_validator
from routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class SendMessageRequest(BaseModel):
    encrypted_content: str
    message_type: str = "text"

    @field_validator("encrypted_content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("encrypted_content cannot be empty.")
        if len(v) > 100_000:
            raise ValueError("Message content too large (max 100KB).")
        return v

    @field_validator("message_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"text", "image", "file", "audio"}
        if v not in allowed:
            raise ValueError(f"message_type must be one of {allowed}.")
        return v


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/conversations",
    summary="List conversations for current user",
)
async def get_conversations(user: dict = Depends(get_current_user)):
    """
    Returns all conversations for the authenticated user.
    Full implementation requires Supabase DB tables.
    """
    return {
        "user_id": user.get("id"),
        "conversations": [],
        "note": "Full conversation list requires Supabase DB setup.",
    }


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="Get messages in a conversation",
)
async def get_messages(
    conversation_id: str = PathParam(..., pattern=r"^[a-zA-Z0-9\-_]{1,64}$"),
    user: dict = Depends(get_current_user),
):
    """
    Returns paginated messages for a conversation.
    TODO: validate that the authenticated user is a member of this conversation.
    """
    return {
        "conversation_id": conversation_id,
        "messages": [],
        "note": "Full message history requires Supabase DB setup.",
    }


@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Send an encrypted message",
)
async def send_message(
    body: SendMessageRequest,
    conversation_id: str = PathParam(..., pattern=r"^[a-zA-Z0-9\-_]{1,64}$"),
    user: dict = Depends(get_current_user),
):
    """
    Stores an encrypted message. The server never decrypts the content.
    Real-time delivery is handled by Socket.io (sockets/chat.py).
    TODO: validate conversation membership before allowing write.
    """
    logger.info(
        f"Message sent in conversation {conversation_id} by user {user.get('id')} "
        f"(type={body.message_type}, size={len(body.encrypted_content)})"
    )
    return {
        "conversation_id": conversation_id,
        "sender_id": user.get("id"),
        "message_type": body.message_type,
        "status": "queued",
        "note": "DB persistence requires Supabase setup. Real-time delivery via Socket.io.",
    }
