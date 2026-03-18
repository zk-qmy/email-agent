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
    approval_status: Optional[Literal["pending", "approved", "edit"]] = None
    followup_count: int = 0
    last_reply: Optional[str] = None
    reply_intent: Optional[Literal["confirmed", "negotiate", "declined"]] = None
    status: Optional[Literal["sent", "failed"]] = None


def merge_mail(current: EmailData, update: EmailData) -> EmailData:
    """Merge email state safely across checkpointed steps.

    MemorySaver deserializes Pydantic models as plain dicts between steps,
    so both branches below normalize to dict before merging.

    Rules:
    - followup_count: always keep the maximum (never let a default-0 reset it)
    - all other fields: only overwrite if the incoming value is not None
    """
    current_dict = current.model_dump() if isinstance(current, EmailData) else dict(current)
    update_dict = update.model_dump() if isinstance(update, EmailData) else dict(update)

    merged = {**current_dict}
    for k, v in update_dict.items():
        if k == "followup_count":
            merged[k] = max(current_dict.get(k, 0), v or 0)
        elif v is not None:
            merged[k] = v
    return EmailData(**merged)


class AgentState(BaseModel):
    messages: List[dict] = Field(default_factory=list)
    workflow: Optional[Literal["schedule", "ticket", "chat"]] = None
    meeting: MeetingData = Field(default_factory=MeetingData)
    email: Annotated[EmailData, merge_mail] = Field(default_factory=EmailData)
    response: Optional[str] = None