from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Optional
from backend.services.mail_service import mail_service

router = APIRouter()


class SendEmailRequest(BaseModel):
    sender_id: int
    recipient_email: str
    subject: str
    body: str


class ReplyEmailRequest(BaseModel):
    sender_id: int
    parent_email_id: int
    body: str


class QueryEmailsRequest(BaseModel):
    user_id: int
    sender_email: Optional[str] = None
    subject_kw: Optional[str] = None
    body_kw: Optional[str] = None
    folder: Optional[str] = None


class MarkReadRequest(BaseModel):
    email_id: int


@router.post("/send")
async def send_email(request: SendEmailRequest):
    result = mail_service.send_email(
        request.sender_id, request.recipient_email, request.subject, request.body
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"email_id": result["email_id"], "message": result["message"]}


@router.post("/reply")
async def reply_email(request: ReplyEmailRequest):
    result = mail_service.reply_email(
        request.sender_id, request.parent_email_id, request.body
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"email_id": result["email_id"], "message": result["message"]}


@router.get("/inbox")
async def get_inbox(user_id: int = Query(...), unread: bool = Query(False)):
    emails = mail_service.get_inbox(user_id, unread)
    return {"emails": [{"email": e} for e in emails]}


@router.get("/sent")
async def get_sent(user_id: int = Query(...)):
    emails = mail_service.get_sent(user_id)
    return {"emails": [{"email": e} for e in emails]}


@router.get("/{email_id}")
async def get_email(email_id: int):
    email = mail_service.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"email": email}


@router.post("/query")
async def query_emails(request: QueryEmailsRequest):
    emails = mail_service.query_emails(
        request.user_id,
        request.sender_email,
        request.subject_kw,
        request.body_kw,
        request.folder,
    )
    return {"emails": emails}


@router.get("/poll")
async def poll_inbox(
    user_id: int = Query(...), last_check: Optional[str] = Query(None)
):
    result = mail_service.poll_inbox(user_id, last_check)
    return result


@router.put("/mark_read")
async def mark_read(request: MarkReadRequest):
    result = mail_service.mark_read(request.email_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"success": True}
