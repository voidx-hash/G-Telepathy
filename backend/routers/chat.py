"""
G Telepathy — Chat Router (Cloudflare D1 backend)

Security:
- All endpoints require a valid Bearer JWT
- conversation_id validated to prevent path traversal
- Messages stored encrypted (server never decrypts content)
- Membership enforced before read/write
"""
import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam
from pydantic import BaseModel, field_validator
from routers.auth import get_current_user
from services.d1 import query, execute, D1Error, D1NotConfiguredError

logger = logging.getLogger(__name__)
router = APIRouter()

_CONV_ID_PATTERN = r"^[a-zA-Z0-9\-_]{1,64}$"


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


def _d1_unavailable(e: Exception) -> HTTPException:
    logger.error("D1 error: %s", e)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database service is unavailable.",
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/conversations", summary="List conversations for current user")
async def get_conversations(user: dict = Depends(get_current_user)):
    """Returns all conversations the authenticated user is a member of."""
    try:
        rows = await query(
            """
            SELECT c.id, c.type, c.name, c.description, c.is_encrypted, c.updated_at,
                   cm.role
            FROM conversations c
            JOIN conversation_members cm ON cm.conversation_id = c.id
            WHERE cm.user_id = ?
            ORDER BY c.updated_at DESC
            LIMIT 50
            """,
            [user["id"]],
        )
        return {"user_id": user["id"], "conversations": rows}
    except D1NotConfiguredError:
        raise HTTPException(status_code=503, detail="Database not configured.")
    except D1Error as e:
        raise _d1_unavailable(e)


@router.post(
    "/conversations",
    status_code=status.HTTP_201_CREATED,
    summary="Create a direct conversation (DM)",
)
async def create_conversation(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """Creates a new direct or group conversation and adds the creator as owner."""
    try:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conv_type = body.get("type", "direct")
        name = body.get("name", "")
        if conv_type not in ("direct", "group", "room"):
            raise HTTPException(status_code=400, detail="Invalid conversation type.")

        await execute(
            "INSERT INTO conversations (id, type, name, is_encrypted, created_by, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?, ?)",
            [conv_id, conv_type, name, user["id"], now, now],
        )
        await execute(
            "INSERT INTO conversation_members (id, conversation_id, user_id, role, joined_at) VALUES (?, ?, ?, 'owner', ?)",
            [str(uuid.uuid4()), conv_id, user["id"], now],
        )
        return {"id": conv_id, "type": conv_type, "created_by": user["id"]}
    except HTTPException:
        raise
    except D1NotConfiguredError:
        raise HTTPException(status_code=503, detail="Database not configured.")
    except D1Error as e:
        raise _d1_unavailable(e)


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="Get messages in a conversation",
)
async def get_messages(
    conversation_id: str = PathParam(..., pattern=_CONV_ID_PATTERN),
    user: dict = Depends(get_current_user),
    limit: int = 50,
    before: str | None = None,
):
    """Returns paginated messages. Only conversation members can read messages."""
    try:
        # Membership check
        membership = await query(
            "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
            [conversation_id, user["id"]],
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this conversation.",
            )

        # Paginated fetch
        if before:
            rows = await query(
                """
                SELECT id, sender_id, encrypted_content, message_type, created_at, is_deleted
                FROM messages
                WHERE conversation_id = ? AND created_at < ? AND is_deleted = 0
                ORDER BY created_at DESC LIMIT ?
                """,
                [conversation_id, before, min(limit, 100)],
            )
        else:
            rows = await query(
                """
                SELECT id, sender_id, encrypted_content, message_type, created_at, is_deleted
                FROM messages
                WHERE conversation_id = ? AND is_deleted = 0
                ORDER BY created_at DESC LIMIT ?
                """,
                [conversation_id, min(limit, 100)],
            )
        return {"conversation_id": conversation_id, "messages": rows}
    except HTTPException:
        raise
    except D1NotConfiguredError:
        raise HTTPException(status_code=503, detail="Database not configured.")
    except D1Error as e:
        raise _d1_unavailable(e)


@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Send an encrypted message",
)
async def send_message(
    body: SendMessageRequest,
    conversation_id: str = PathParam(..., pattern=_CONV_ID_PATTERN),
    user: dict = Depends(get_current_user),
):
    """
    Stores an encrypted message in D1. The server never decrypts the content.
    Real-time delivery is handled by Socket.io.
    """
    try:
        # Membership check
        membership = await query(
            "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
            [conversation_id, user["id"]],
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this conversation.",
            )

        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        await execute(
            """
            INSERT INTO messages (id, conversation_id, sender_id, encrypted_content, message_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [msg_id, conversation_id, user["id"], body.encrypted_content, body.message_type, now, now],
        )

        # Update conversation updated_at
        await execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            [now, conversation_id],
        )

        logger.info("Message %s sent in conv %s by user %s", msg_id, conversation_id, user["id"])
        return {
            "id": msg_id,
            "conversation_id": conversation_id,
            "sender_id": user["id"],
            "message_type": body.message_type,
            "status": "sent",
            "created_at": now,
        }
    except HTTPException:
        raise
    except D1NotConfiguredError:
        raise HTTPException(status_code=503, detail="Database not configured.")
    except D1Error as e:
        raise _d1_unavailable(e)
