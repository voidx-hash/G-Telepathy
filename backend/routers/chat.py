"""G Telepathy — Chat Router"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/conversations")
async def get_conversations():
    return {"conversations": []}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    return {"messages": []}


@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str):
    return {"message": "sent"}
