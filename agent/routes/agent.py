from pydantic import BaseModel
from typing import Optional, List
from fastapi import WebSocket, WebSocketDisconnect
from agent.services.agent_service import agent_service, ws_connections


class CreateDraftRequest(BaseModel):
    user_id: int
    recipient: str
    subject: str
    context: str


class UpdateDraftRequest(BaseModel):
    body: Optional[str] = None
    subject: Optional[str] = None


class SendDraftRequest(BaseModel):
    edited_body: Optional[str] = None


class ProcessRequest(BaseModel):
    user_id: int
    email_id: int


class ChatRequest(BaseModel):
    thread_id: str
    message: str


class NegotiateRequest(BaseModel):
    date: str
    time: str


async def create_draft(request: CreateDraftRequest):
    result = agent_service.create_draft(
        user_id=request.user_id,
        recipient=request.recipient,
        subject=request.subject,
        context=request.context,
    )
    return result


async def get_draft(draft_id: str):
    result = agent_service.get_draft(draft_id)
    if not result:
        return {"error": "Draft not found"}, 404
    return result


async def update_draft(draft_id: str, request: UpdateDraftRequest):
    result = agent_service.update_draft(
        draft_id=draft_id,
        body=request.body,
        subject=request.subject,
    )
    if "error" in result:
        return result, 400
    return result


async def send_draft(draft_id: str, request: SendDraftRequest):
    result = await agent_service.send_draft(
        draft_id=draft_id,
        edited_body=request.edited_body,
    )
    if "error" in result:
        return result, 400
    return result


async def cancel_draft(draft_id: str):
    result = agent_service.cancel_draft(draft_id)
    if "error" in result:
        return result, 400
    return result


async def get_user_drafts(user_id: int, status: Optional[str] = None):
    result = agent_service.get_user_drafts(user_id, status)
    return {"drafts": result}


async def get_thread(thread_id: str):
    result = agent_service.get_thread(thread_id)
    if not result:
        return {"error": "Thread not found"}, 404
    return result


async def get_user_threads(user_id: int, status: Optional[str] = None):
    result = agent_service.get_user_threads(user_id, status)
    return {"threads": result}


async def confirm_meeting(thread_id: str):
    result = await agent_service.confirm_meeting(thread_id)
    if "error" in result:
        return result, 400
    return result


async def negotiate_meeting(thread_id: str, request: NegotiateRequest):
    result = await agent_service.negotiate_meeting(
        thread_id=thread_id,
        date=request.date,
        time=request.time,
    )
    if "error" in result:
        return result, 400
    return result


async def decline_meeting(thread_id: str):
    result = await agent_service.decline_meeting(thread_id)
    if "error" in result:
        return result, 400
    return result


active_workflows = {}


async def process_email(request: ProcessRequest):
    result = await agent_service.process_email(request.user_id, request.email_id)
    return result


async def chat(request: ChatRequest):
    result = agent_service.chat(request.thread_id, request.message, active_workflows)
    return result


async def get_status(thread_id: str):
    result = agent_service.get_status(thread_id, active_workflows)
    if "error" in result:
        return result, 404
    return result


async def get_history(thread_id: str):
    result = agent_service.get_history(thread_id, active_workflows)
    if "error" in result:
        return result, 404
    return result


async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    agent_service.add_websocket(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")

            if event == "ping":
                await websocket.send_json({"event": "pong"})

            elif event == "poll":
                thread_id = data.get("thread_id")
                if thread_id:
                    from agent.services.agent_service import threads
                    thread = threads.get(thread_id)
                    if thread:
                        await websocket.send_json({
                            "event": "status",
                            "thread_id": thread_id,
                            "status": thread["status"],
                            "reply_intent": thread["reply_intent"],
                        })

            elif event == "subscribe":
                thread_id = data.get("thread_id")
                await websocket.send_json({
                    "event": "subscribed",
                    "thread_id": thread_id,
                })

    except WebSocketDisconnect:
        agent_service.remove_websocket(user_id, websocket)
    except Exception as e:
        await websocket.send_json({
            "event": "error",
            "message": str(e)
        })
        agent_service.remove_websocket(user_id, websocket)
