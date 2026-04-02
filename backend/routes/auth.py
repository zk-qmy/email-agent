from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from backend.services.mail_service import mail_service
from backend.database import SessionLocal
from backend.models import User
from werkzeug.security import generate_password_hash

router = APIRouter()


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


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


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = mail_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}


@router.put("/users/{user_id}")
async def update_user(user_id: int, request: UpdateUserRequest):
    result = mail_service.update_user(
        user_id,
        username=request.username,
        email=request.email,
        password=request.password,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"user": result["user"]}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    result = mail_service.delete_user(user_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"success": True}


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
