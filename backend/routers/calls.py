"""
G Telepathy — Calls Router

Security:
- All endpoints require a valid Bearer token (get_current_user)
- Path params validated for safe characters
- No stack traces exposed (global handler in main.py catches everything)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam
from pydantic import BaseModel
from routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

_SAFE_ID_PATTERN = r"^[a-zA-Z0-9\-_]{1,64}$"


class InitiateCallRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}
    target_user_id: str
    call_type: str = "audio"  # "audio" | "video"


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post(
    "/initiate",
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a call",
    description="Creates a call session. Actual signaling happens via Socket.io.",
)
async def initiate_call(
    body: InitiateCallRequest,
    user: dict = Depends(get_current_user),
):
    if body.call_type not in ("audio", "video"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="call_type must be 'audio' or 'video'.",
        )
    caller_id = user.get("id")
    logger.info(f"Call initiated by {caller_id} → {body.target_user_id}")
    return {
        "caller_id": caller_id,
        "target_user_id": body.target_user_id,
        "call_type": body.call_type,
        "status": "ringing",
        "note": "Connect via Socket.io to complete WebRTC signaling.",
    }


@router.post(
    "/{call_id}/end",
    status_code=status.HTTP_200_OK,
    summary="End an active call",
)
async def end_call(
    call_id: str = PathParam(..., pattern=r"^[a-zA-Z0-9\-_]{1,64}$"),
    user: dict = Depends(get_current_user),
):
    logger.info(f"Call {call_id} ended by user {user.get('id')}")
    return {"call_id": call_id, "status": "ended"}


@router.get(
    "/history",
    summary="Get call history for current user",
)
async def call_history(user: dict = Depends(get_current_user)):
    """
    Returns call history for the authenticated user.
    Full DB integration requires Supabase tables to be provisioned.
    """
    return {
        "user_id": user.get("id"),
        "calls": [],
        "note": "Full call history requires Supabase DB setup.",
    }
