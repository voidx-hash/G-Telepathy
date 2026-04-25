"""G Telepathy — Auth Router"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    """Register a new user via Supabase Auth."""
    return {"message": "register endpoint — coming soon"}


@router.post("/login")
async def login():
    """Authenticate user and return JWT."""
    return {"message": "login endpoint — coming soon"}


@router.post("/logout")
async def logout():
    return {"message": "logout endpoint — coming soon"}


@router.get("/me")
async def get_me():
    return {"message": "get current user — coming soon"}
