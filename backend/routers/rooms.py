"""
G Telepathy — Global Rooms Router

Security:
- Listing rooms is public (no auth required — rooms are discoverable)
- Creating and joining rooms requires authentication
- room_id path params validated to prevent path traversal
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam
from pydantic import BaseModel, field_validator
from routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


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


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="List all public rooms",
    description="Returns a list of public global rooms. No authentication required.",
)
async def list_rooms():
    """Public endpoint — anyone can browse rooms."""
    return {
        "rooms": [],
        "note": "Full room list requires Supabase DB setup.",
    }


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
)
async def create_room(
    body: CreateRoomRequest,
    user: dict = Depends(get_current_user),
):
    logger.info(f"Room '{body.name}' created by user {user.get('id')}")
    return {
        "name": body.name,
        "topic": body.topic,
        "language": body.language,
        "is_private": body.is_private,
        "owner_id": user.get("id"),
        "status": "created",
        "note": "DB persistence requires Supabase setup.",
    }


@router.post(
    "/{room_id}/join",
    summary="Join a room",
)
async def join_room(
    room_id: str = PathParam(..., pattern=r"^[a-zA-Z0-9\-_]{1,64}$"),
    user: dict = Depends(get_current_user),
):
    logger.info(f"User {user.get('id')} joining room {room_id}")
    return {"room_id": room_id, "user_id": user.get("id"), "status": "joined"}


@router.post(
    "/{room_id}/leave",
    summary="Leave a room",
)
async def leave_room(
    room_id: str = PathParam(..., pattern=r"^[a-zA-Z0-9\-_]{1,64}$"),
    user: dict = Depends(get_current_user),
):
    logger.info(f"User {user.get('id')} leaving room {room_id}")
    return {"room_id": room_id, "user_id": user.get("id"), "status": "left"}
