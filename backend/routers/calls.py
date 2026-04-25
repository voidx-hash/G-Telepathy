"""G Telepathy — Calls Router"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/initiate")
async def initiate_call():
    return {"call_id": "placeholder", "status": "ringing"}


@router.post("/{call_id}/end")
async def end_call(call_id: str):
    return {"status": "ended"}


@router.get("/history")
async def call_history():
    return {"calls": []}
