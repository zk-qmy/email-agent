from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DraftContent(BaseModel):
    recipient: str
    subject: str
    body: str


class Draft(BaseModel):
    draft_id: str
    draft: DraftContent
    status: str
    user_id: int
    context: str
    thread_id: Optional[str] = None
    email_id: Optional[str] = None
    created_at: str
    sent_at: Optional[str] = None
    updated_at: Optional[str] = None


class DraftCreate(BaseModel):
    user_id: int
    recipient: str
    subject: str
    context: str


class DraftUpdate(BaseModel):
    body: Optional[str] = None
    subject: Optional[str] = None


class DraftSend(BaseModel):
    edited_body: Optional[str] = None
