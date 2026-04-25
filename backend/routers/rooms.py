"""G Telepathy — Global Rooms Router"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_rooms():
    return {"rooms": []}


@router.post("/")
async def create_room():
    return {"message": "room created"}


@router.post("/{room_id}/join")
async def join_room(room_id: str):
    return {"status": "joined"}


@router.post("/{room_id}/leave")
async def leave_room(room_id: str):
    return {"status": "left"}
