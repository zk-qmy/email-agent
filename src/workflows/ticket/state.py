from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional
from src.state.base import BaseState


class RequestData(BaseModel):
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    gpa: Optional[float] = None
    credits_completed: Optional[int] = None
    reason: Optional[str] = None          # Why they need the AA
    advisor_email: Optional[str] = None
    registrar_email: Optional[str] = None
    is_eligible: Optional[bool] = None
    eligibility_notes: Optional[str] = None


class EmailData(BaseModel):
    draft: Optional[str] = None
    approval_status: Optional[
        Literal["pending", "approved", "edit", "cancelled"]
    ] = None
    nudge_count: int = 0
    last_reply: Optional[str] = None
    reply_intent: Optional[
        Literal["approved", "needs_info", "rejected", "issue_detected"]
    ] = None
    status: Optional[Literal["sent", "failed"]] = None
    # For needs_info branch
    search_result: Optional[Literal["found", "not_found"]] = None
    # For self-correct branch
    self_correct_result: Optional[Literal["fixed", "not_fixed"]] = None


def merge_ticket_mail(current: EmailData, update: EmailData) -> EmailData:
    """Merge only explicitly set (non-None) fields from update into current.
    Similar to merge_mail but with ticket-specific fields and intents.
    """
    if isinstance(update, dict):
        # Dict updates: only merge the keys explicitly provided
        current_dict = current.model_dump()
        current_dict.update(update)
        return EmailData(**current_dict)
    # EmailData object: merge only fields that are not None,
    # but treat nudge_count specially — always take the max to avoid reset.
    current_dict = current.model_dump()
    update_dict = update.model_dump()

    merged = {**current_dict}
    for k, v in update_dict.items():
        if k == "nudge_count":
            # Always keep the higher count so increment is never lost
            merged[k] = max(current_dict[k], v)
        elif v is not None:
            merged[k] = v
    return EmailData(**merged)


class TicketState(BaseState):
    # Define any additional fields specific to the ticket workflow here
    ticket_request: RequestData = Field(default_factory=RequestData)
    aa_email: Annotated[EmailData, merge_ticket_mail] = Field(default_factory=EmailData)
    registrar_email: Annotated[EmailData, merge_ticket_mail] = Field(default_factory=EmailData)
