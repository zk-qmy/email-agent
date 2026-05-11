from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Response, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, Field, EmailStr
from backend.services.mail_service import mail_service
from backend.database import SessionLocal
from backend.models import User
from werkzeug.security import generate_password_hash
import os

router = APIRouter()
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production-32chars")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire.isoformat()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = mail_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"id": user["id"], "username": user["username"], "email": user["email"], "role": user.get("role", "student")}


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=1)
    role: Optional[str] = None


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
                {"id": u.id, "username": u.username, "email": u.email, "role": u.role} for u in users
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
    result = mail_service.signup(request.username, request.email, request.password, role=request.role or "student")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"user_id": result["user_id"], "message": result["message"]}


@router.post("/login")
async def login(request: LoginRequest, response: Response):
    result = mail_service.login(request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    
    access_token = create_access_token(
        data={"user_id": result["user_id"], "email": result["email"]},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        samesite="lax"
    )
    
    return {
        "user_id": result["user_id"],
        "username": result["username"],
        "email": result["email"],
        "role": result.get("role", "student"),
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}