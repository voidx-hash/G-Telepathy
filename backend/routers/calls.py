"""
G Telepathy — Calls Router (Cloudflare D1)

Security:
- All endpoints require a valid Bearer token
- Path params validated for safe characters
- call_id stored in D1 to track session state
"""
import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam
from pydantic import BaseModel
from routers.auth import get_current_user
from services.d1 import query, execute, D1Error, D1NotConfiguredError

logger = logging.getLogger(__name__)
router = APIRouter()

_SAFE_ID_PATTERN = r"^[a-zA-Z0-9\-_]{1,64}$"


class InitiateCallRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}
    target_user_id: str
    call_type: str = "audio"  # "audio" | "video"


def _d1_unavailable(e: Exception) -> HTTPException:
    logger.error("D1 error: %s", e)
    return HTTPException(status_code=503, detail="Database service is unavailable.")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post(
    "/initiate",
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a call",
    description="Creates a call log entry. Actual signaling happens via Socket.io.",
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
    call_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    try:
        await execute(
            """
            INSERT INTO call_logs (id, caller_id, callee_id, call_type, status, created_at)
            VALUES (?, ?, ?, ?, 'ringing', ?)
            """,
            [call_id, caller_id, body.target_user_id, body.call_type, now],
        )
    except D1NotConfiguredError:
        pass  # Log entry is best-effort; Socket.io signaling still works
    except D1Error as e:
        logger.warning("Could not log call to D1: %s", e)

    logger.info("Call %s initiated by %s → %s", call_id, caller_id, body.target_user_id)
    return {
        "call_id": call_id,
        "caller_id": caller_id,
        "target_user_id": body.target_user_id,
        "call_type": body.call_type,
        "status": "ringing",
    }


@router.post(
    "/{call_id}/end",
    status_code=status.HTTP_200_OK,
    summary="End an active call",
)
async def end_call(
    call_id: str = PathParam(..., pattern=_SAFE_ID_PATTERN),
    user: dict = Depends(get_current_user),
):
    now = datetime.now(timezone.utc).isoformat()
    try:
        await execute(
            "UPDATE call_logs SET status = 'ended', ended_at = ? WHERE id = ? AND (caller_id = ? OR callee_id = ?)",
            [now, call_id, user["id"], user["id"]],
        )
    except (D1NotConfiguredError, D1Error) as e:
        logger.warning("Could not update call log in D1: %s", e)

    logger.info("Call %s ended by user %s", call_id, user["id"])
    return {"call_id": call_id, "status": "ended"}


@router.get(
    "/history",
    summary="Get call history for current user",
)
async def call_history(user: dict = Depends(get_current_user), limit: int = 20):
    """Returns call history for the authenticated user from D1."""
    try:
        rows = await query(
            """
            SELECT id, caller_id, callee_id, call_type, status, created_at, ended_at
            FROM call_logs
            WHERE caller_id = ? OR callee_id = ?
            ORDER BY created_at DESC LIMIT ?
            """,
            [user["id"], user["id"], min(limit, 50)],
        )
        return {"user_id": user["id"], "calls": rows}
    except D1NotConfiguredError:
        return {"user_id": user["id"], "calls": [], "note": "Database not configured."}
    except D1Error as e:
        raise _d1_unavailable(e)
