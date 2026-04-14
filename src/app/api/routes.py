from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.app.sessions.manager import SessionManager

router = APIRouter()
manager = SessionManager()   # one manager, shared across all requests


class MessageRequest(BaseModel):
    content:       str
    workflow_name: Optional[str] = None  # only needed on first message


@router.post("/chat/{conversation_id}")
async def send_message(conversation_id: str, req: MessageRequest):
    user_message = {"role": "user", "content": req.content}
    try:
        result = await manager.handle_message(
            conversation_id=conversation_id,
            user_message=user_message,
            workflow_name=req.workflow_name,
        )
        return {
            "conversation_id": conversation_id,
            "response":        result.get("response"),
            "interrupted":     "__interrupt__" in result,
            "interrupt_data":  result.get("__interrupt__", [None])[0].value
                               if "__interrupt__" in result else None,
            "status":          manager.get_status(conversation_id),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chat/{conversation_id}/status")
async def get_status(conversation_id: str):
    return {"status": manager.get_status(conversation_id)}
