"""
G Telepathy — Global Rooms Router (Cloudflare D1)

Security:
- Listing rooms is public — rooms are discoverable
- Creating, joining, leaving requires authentication
- room_id path validated to prevent path traversal
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

_ROOM_ID_PATTERN = r"^[a-zA-Z0-9\-_]{1,64}$"


class CreateRoomRequest(BaseModel):
    name: str
    topic: str = ""
    language: str = "en"
    is_private: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 80:
            raise ValueError("Room name must be between 2 and 80 characters.")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        v = v.strip().lower()
        if not all(c.isalpha() or c == "-" for c in v) or len(v) > 10:
            raise ValueError("Invalid language code.")
        return v


def _d1_unavailable(e: Exception) -> HTTPException:
    logger.error("D1 error: %s", e)
    return HTTPException(status_code=503, detail="Database service is unavailable.")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="List all public rooms",
    description="Returns public global rooms. No authentication required.",
)
async def list_rooms(language: str | None = None, limit: int = 20):
    """Public endpoint — anyone can browse rooms."""
    try:
        if language:
            if not all(c.isalpha() or c == "-" for c in language) or len(language) > 10:
                raise HTTPException(status_code=400, detail="Invalid language code.")
            rows = await query(
                "SELECT id, name, topic, language, is_public, member_count, created_at FROM rooms WHERE is_public = 1 AND language = ? ORDER BY member_count DESC LIMIT ?",
                [language, min(limit, 50)],
            )
        else:
            rows = await query(
                "SELECT id, name, topic, language, is_public, member_count, created_at FROM rooms WHERE is_public = 1 ORDER BY member_count DESC LIMIT ?",
                [min(limit, 50)],
            )
        return {"rooms": rows}
    except HTTPException:
        raise
    except D1NotConfiguredError:
        return {"rooms": [], "note": "Database not configured yet."}
    except D1Error as e:
        raise _d1_unavailable(e)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
)
async def create_room(
    body: CreateRoomRequest,
    user: dict = Depends(get_current_user),
):
    try:
        room_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await execute(
            """
            INSERT INTO rooms (id, name, topic, language, is_public, member_count, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """,
            [room_id, body.name, body.topic, body.language, 0 if body.is_private else 1, user["id"], now],
        )
        logger.info("Room '%s' (%s) created by user %s", body.name, room_id, user["id"])
        return {
            "id": room_id,
            "name": body.name,
            "topic": body.topic,
            "language": body.language,
            "is_private": body.is_private,
            "owner_id": user["id"],
        }
    except D1NotConfiguredError:
        raise HTTPException(status_code=503, detail="Database not configured.")
    except D1Error as e:
        raise _d1_unavailable(e)


@router.post("/{room_id}/join", summary="Join a room")
async def join_room(
    room_id: str = PathParam(..., pattern=_ROOM_ID_PATTERN),
    user: dict = Depends(get_current_user),
):
    try:
        # Check room exists
        rooms = await query("SELECT id, is_public FROM rooms WHERE id = ?", [room_id])
        if not rooms:
            raise HTTPException(status_code=404, detail="Room not found.")

        # Upsert membership
        now = datetime.now(timezone.utc).isoformat()
        existing = await query(
            "SELECT 1 FROM room_members WHERE room_id = ? AND user_id = ?",
            [room_id, user["id"]],
        )
        if not existing:
            await execute(
                "INSERT INTO room_members (id, room_id, user_id, joined_at) VALUES (?, ?, ?, ?)",
                [str(uuid.uuid4()), room_id, user["id"], now],
            )
            await execute(
                "UPDATE rooms SET member_count = member_count + 1 WHERE id = ?",
                [room_id],
            )

        logger.info("User %s joined room %s", user["id"], room_id)
        return {"room_id": room_id, "user_id": user["id"], "status": "joined"}
    except HTTPException:
        raise
    except D1NotConfiguredError:
        raise HTTPException(status_code=503, detail="Database not configured.")
    except D1Error as e:
        raise _d1_unavailable(e)


@router.post("/{room_id}/leave", summary="Leave a room")
async def leave_room(
    room_id: str = PathParam(..., pattern=_ROOM_ID_PATTERN),
    user: dict = Depends(get_current_user),
):
    try:
        await execute(
            "DELETE FROM room_members WHERE room_id = ? AND user_id = ?",
            [room_id, user["id"]],
        )
        await execute(
            "UPDATE rooms SET member_count = MAX(0, member_count - 1) WHERE id = ?",
            [room_id],
        )
        logger.info("User %s left room %s", user["id"], room_id)
        return {"room_id": room_id, "user_id": user["id"], "status": "left"}
    except D1NotConfiguredError:
        raise HTTPException(status_code=503, detail="Database not configured.")
    except D1Error as e:
        raise _d1_unavailable(e)
