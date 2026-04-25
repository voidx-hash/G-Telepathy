"""G Telepathy — Chat Socket.io Event Handlers"""
import socketio


def register(sio: socketio.AsyncServer):
    @sio.event
    async def connect(sid, environ, auth):
        print(f"[Socket] Client connected: {sid}")

    @sio.event
    async def disconnect(sid):
        print(f"[Socket] Client disconnected: {sid}")

    @sio.on("join_conversation")
    async def join_conversation(sid, data):
        conversation_id = data.get("conversation_id")
        await sio.enter_room(sid, f"conversation:{conversation_id}")
        await sio.emit("joined", {"conversation_id": conversation_id}, to=sid)

    @sio.on("send_message")
    async def send_message(sid, data):
        """
        Expected data:
        {
            "conversation_id": str,
            "encrypted_content": str,  # AES-256 client-side encrypted
            "message_type": str
        }
        """
        conversation_id = data.get("conversation_id")
        # Broadcast encrypted message to all room members
        await sio.emit(
            "new_message",
            data,
            room=f"conversation:{conversation_id}",
            skip_sid=sid,
        )

    @sio.on("typing")
    async def typing(sid, data):
        conversation_id = data.get("conversation_id")
        await sio.emit(
            "user_typing",
            data,
            room=f"conversation:{conversation_id}",
            skip_sid=sid,
        )
