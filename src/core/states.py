from __future__ import annotations
from typing import Annotated, List, Literal, Optional
from pydantic import BaseModel, Field


class MeetingData(BaseModel):
    participants: List[str] = Field(default_factory=list)
    date: Optional[str] = None
    time: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)


class EmailData(BaseModel):
    draft: Optional[str] = None
    approval_status: Optional[Literal["pending", "approved", "edit", "cancelled"]] = (
        None
    )
    followup_count: int = 0
    last_reply: Optional[str] = None
    reply_intent: Optional[Literal["confirmed", "negotiate", "declined"]] = None
    status: Optional[Literal["sent", "failed", "pending"]] = None


def merge_mail(current: EmailData, update: EmailData) -> EmailData:
    """Merge only explicitly set (non-None) fields from update into current.
    BUG_FIX: The original filter 'if v is not None' correctly keeps 0,
    but EmailData(followup_count=new_count) still sets all OTHER fields to
    their defaults (None/0), which then overwrite valid state values.
    Fix: only merge fields that differ from a fresh EmailData() default,
    OR the caller must pass only the changed fields via model_copy.
    Simplest robust fix: accept a dict directly and only merge provided keys.
    """
    if isinstance(update, dict):
        # Dict updates: only merge the keys explicitly provided
        current_dict = current.model_dump()
        current_dict.update(update)
        return EmailData(**current_dict)
    # EmailData object: merge only fields that are not None,
    # but treat followup_count specially — always take the max to avoid reset.
    current_dict = current.model_dump()
    update_dict = update.model_dump()

    merged = {**current_dict}
    for k, v in update_dict.items():
        if k == "followup_count":
            # Always keep the higher count so increment is never lost
            merged[k] = max(current_dict[k], v)
        elif v is not None:
            merged[k] = v
    return EmailData(**merged)


class AgentState(BaseModel):
    messages: List[dict] = Field(default_factory=list)
    workflow: Optional[Literal["schedule", "ticket", "chat"]] = None
    email_id: Optional[int] = None
    meeting: MeetingData = Field(default_factory=MeetingData)
    # BUG_FIX: Added Field(default_factory=EmailData) so Pydantic has a default.
    email: Annotated[EmailData, merge_mail] = Field(default_factory=EmailData)
    response: Optional[str] = None
