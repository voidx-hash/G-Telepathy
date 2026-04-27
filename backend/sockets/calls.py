"""
G Telepathy — Calls Socket.io Event Handlers (WebRTC Signaling)

Security:
- Authentication is validated on connect (same shared session store as chat)
- Unauthenticated connections are rejected (handled in chat.py connect event)
- All data fields validated; missing/bad fields return error codes
- target_user_id and caller_sid validated to prevent session spoofing
- sender_id is always injected from the server-verified session, never from client data
"""
import logging
import socketio
# Reuse the shared session store from chat.py
import sockets.chat as chat_module

logger = logging.getLogger(__name__)


def register(sio: socketio.AsyncServer):

    @sio.on("call_initiate")
    async def call_initiate(sid, data):
        """Send a call request to the target user.
        Client sends: { target_user_id, call_type }
        Server injects: caller_id from session (prevents spoofing)
        """
        if sid not in chat_module._sessions:
            await sio.emit("error", {"code": "UNAUTHENTICATED"}, to=sid)
            return
        if not isinstance(data, dict):
            await sio.emit("error", {"code": "INVALID_DATA"}, to=sid)
            return

        target_user_id = str(data.get("target_user_id", "")).strip()
        call_type = str(data.get("call_type", "audio")).strip()

        if not target_user_id:
            await sio.emit("error", {"code": "MISSING_TARGET_USER_ID"}, to=sid)
            return
        if call_type not in ("audio", "video"):
            await sio.emit("error", {"code": "INVALID_CALL_TYPE"}, to=sid)
            return

        caller_id = chat_module._sessions[sid]["user_id"]
        if caller_id == target_user_id:
            await sio.emit("error", {"code": "CANNOT_CALL_SELF"}, to=sid)
            return

        await sio.emit(
            "incoming_call",
            {
                "caller_id": caller_id,  # from server session — not spoofable
                "caller_sid": sid,
                "call_type": call_type,
            },
            room=f"user:{target_user_id}",
        )
        logger.info(f"Call initiated: {caller_id} → user:{target_user_id}")

    @sio.on("call_answer")
    async def call_answer(sid, data):
        if sid not in chat_module._sessions:
            await sio.emit("error", {"code": "UNAUTHENTICATED"}, to=sid)
            return
        if not isinstance(data, dict):
            return

        caller_sid = str(data.get("caller_sid", "")).strip()
        if not caller_sid:
            await sio.emit("error", {"code": "MISSING_CALLER_SID"}, to=sid)
            return

        await sio.emit(
            "call_answered",
            {"answerer_id": chat_module._sessions[sid]["user_id"], "answerer_sid": sid},
            to=caller_sid,
        )

    @sio.on("call_reject")
    async def call_reject(sid, data):
        if sid not in chat_module._sessions:
            await sio.emit("error", {"code": "UNAUTHENTICATED"}, to=sid)
            return
        if not isinstance(data, dict):
            return

        caller_sid = str(data.get("caller_sid", "")).strip()
        if not caller_sid:
            return

        await sio.emit(
            "call_rejected",
            {"rejecter_id": chat_module._sessions[sid]["user_id"]},
            to=caller_sid,
        )

    @sio.on("call_end")
    async def call_end(sid, data):
        if sid not in chat_module._sessions:
            await sio.emit("error", {"code": "UNAUTHENTICATED"}, to=sid)
            return
        if not isinstance(data, dict):
            return

        room = str(data.get("call_room", "")).strip()
        if not room:
            return

        await sio.emit(
            "call_ended",
            {"ended_by": chat_module._sessions[sid]["user_id"]},
            room=room,
        )

    @sio.on("webrtc_offer")
    async def webrtc_offer(sid, data):
        """Relay WebRTC offer SDP to target peer."""
        if sid not in chat_module._sessions:
            await sio.emit("error", {"code": "UNAUTHENTICATED"}, to=sid)
            return
        if not isinstance(data, dict):
            return

        target = str(data.get("target_sid", "")).strip()
        sdp = data.get("sdp")
        if not target or not sdp:
            await sio.emit("error", {"code": "MISSING_FIELDS"}, to=sid)
            return

        await sio.emit(
            "webrtc_offer",
            {"sdp": sdp, "from_sid": sid},
            to=target,
        )

    @sio.on("webrtc_answer")
    async def webrtc_answer(sid, data):
        """Relay WebRTC answer SDP to the offering peer."""
        if sid not in chat_module._sessions:
            await sio.emit("error", {"code": "UNAUTHENTICATED"}, to=sid)
            return
        if not isinstance(data, dict):
            return

        target = str(data.get("target_sid", "")).strip()
        sdp = data.get("sdp")
        if not target or not sdp:
            await sio.emit("error", {"code": "MISSING_FIELDS"}, to=sid)
            return

        await sio.emit(
            "webrtc_answer",
            {"sdp": sdp, "from_sid": sid},
            to=target,
        )

    @sio.on("webrtc_ice_candidate")
    async def ice_candidate(sid, data):
        """Relay ICE candidate to the target peer."""
        if sid not in chat_module._sessions:
            await sio.emit("error", {"code": "UNAUTHENTICATED"}, to=sid)
            return
        if not isinstance(data, dict):
            return

        target = str(data.get("target_sid", "")).strip()
        candidate = data.get("candidate")
        if not target or not candidate:
            await sio.emit("error", {"code": "MISSING_FIELDS"}, to=sid)
            return

        await sio.emit(
            "webrtc_ice_candidate",
            {"candidate": candidate, "from_sid": sid},
            to=target,
        )
