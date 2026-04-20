import asyncio
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConversationSession:
    conversation_id: str
    workflow_name:   str
    task:            Optional[asyncio.Task] = field(default=None, repr=False)
    status:          str = "idle"
    # status values: idle | running | waiting_interrupt | done | error
