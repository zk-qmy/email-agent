from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.mail_service import mail_service
from backend.database import SessionLocal
from backend.models import User

router = APIRouter()


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.get("/users")
async def get_users():
    session = SessionLocal()
    try:
        users = session.query(User).all()
        return {
            "users": [
                {"id": u.id, "username": u.username, "email": u.email} for u in users
            ]
        }
    finally:
        session.close()


@router.post("/signup")
async def signup(request: SignupRequest):
    result = mail_service.signup(request.username, request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"user_id": result["user_id"], "message": result["message"]}


@router.post("/login")
async def login(request: LoginRequest):
    result = mail_service.login(request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return {
        "user_id": result["user_id"],
        "username": result["username"],
        "email": result["email"],
    }
