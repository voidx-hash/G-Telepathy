"""G Telepathy — Calls Socket.io Event Handlers (WebRTC Signaling)"""
import socketio


def register(sio: socketio.AsyncServer):
    @sio.on("call_initiate")
    async def call_initiate(sid, data):
        """Send call request to target user."""
        target_user_id = data.get("target_user_id")
        await sio.emit("incoming_call", data, room=f"user:{target_user_id}")

    @sio.on("call_answer")
    async def call_answer(sid, data):
        caller_sid = data.get("caller_sid")
        await sio.emit("call_answered", data, to=caller_sid)

    @sio.on("call_reject")
    async def call_reject(sid, data):
        caller_sid = data.get("caller_sid")
        await sio.emit("call_rejected", data, to=caller_sid)

    @sio.on("call_end")
    async def call_end(sid, data):
        room = data.get("call_room")
        await sio.emit("call_ended", data, room=room)

    @sio.on("webrtc_offer")
    async def webrtc_offer(sid, data):
        target = data.get("target_sid")
        await sio.emit("webrtc_offer", data, to=target)

    @sio.on("webrtc_answer")
    async def webrtc_answer(sid, data):
        target = data.get("target_sid")
        await sio.emit("webrtc_answer", data, to=target)

    @sio.on("webrtc_ice_candidate")
    async def ice_candidate(sid, data):
        target = data.get("target_sid")
        await sio.emit("webrtc_ice_candidate", data, to=target)
