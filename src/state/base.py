from typing import Optional, List
from pydantic import BaseModel, Field


class BaseState(BaseModel):
    conversation_id: str = ""   # matches LangGraph thread_id
    messages: List[dict] = Field(
        default_factory=list)  # full conversation history
    workflow: Optional[str] = None
    response: Optional[str] = None
