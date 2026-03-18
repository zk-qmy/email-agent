import os
import asyncio
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from agent.routes.agent import (
    CreateDraftRequest,
    UpdateDraftRequest,
    SendDraftRequest,
    ProcessRequest,
    ChatRequest,
    NegotiateRequest,
    create_draft,
    get_draft,
    update_draft,
    send_draft,
    cancel_draft,
    get_user_drafts,
    get_thread,
    get_user_threads,
    confirm_meeting,
    negotiate_meeting,
    decline_meeting,
    process_email,
    chat,
    get_status,
    get_history,
    websocket_endpoint,
)

app = FastAPI(title="Email Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/agent/draft")
async def agent_create_draft(request: CreateDraftRequest):
    return await create_draft(request)


@app.get("/api/agent/draft/{draft_id}")
async def agent_get_draft(draft_id: str):
    return await get_draft(draft_id)


@app.put("/api/agent/draft/{draft_id}")
async def agent_update_draft(draft_id: str, request: UpdateDraftRequest):
    return await update_draft(draft_id, request)


@app.post("/api/agent/draft/{draft_id}/send")
async def agent_send_draft(draft_id: str, request: SendDraftRequest):
    return await send_draft(draft_id, request)


@app.delete("/api/agent/draft/{draft_id}")
async def agent_cancel_draft(draft_id: str):
    return await cancel_draft(draft_id)


@app.get("/api/agent/drafts")
async def agent_list_drafts(user_id: int, status: Optional[str] = None):
    return await get_user_drafts(user_id, status)


@app.get("/api/agent/thread/{thread_id}")
async def agent_get_thread(thread_id: str):
    return await get_thread(thread_id)


@app.get("/api/agent/threads")
async def agent_list_threads(user_id: int, status: Optional[str] = None):
    return await get_user_threads(user_id, status)


@app.post("/api/agent/thread/{thread_id}/confirm")
async def agent_confirm_meeting(thread_id: str):
    return await confirm_meeting(thread_id)


@app.post("/api/agent/thread/{thread_id}/negotiate")
async def agent_negotiate_meeting(thread_id: str, request: NegotiateRequest):
    return await negotiate_meeting(thread_id, request)


@app.post("/api/agent/thread/{thread_id}/decline")
async def agent_decline_meeting(thread_id: str):
    return await decline_meeting(thread_id)


@app.post("/api/agent/process")
async def agent_process(request: ProcessRequest):
    return await process_email(request)


@app.post("/api/agent/chat")
async def agent_chat(request: ChatRequest):
    return await chat(request)


@app.get("/api/agent/status/{thread_id}")
async def agent_status(thread_id: str):
    return await get_status(thread_id)


@app.get("/api/agent/history/{thread_id}")
async def agent_history(thread_id: str):
    return await get_history(thread_id)


@app.websocket("/api/agent/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int):
    await websocket_endpoint(websocket, user_id)


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup():
    from agent.services.ws_client import backend_ws_client
    from agent.services.agent_service import agent_service

    backend_ws_client.set_push_handler(agent_service.handle_backend_push)
    backend_ws_client._running = True


@app.on_event("shutdown")
async def shutdown():
    from agent.services.ws_client import backend_ws_client
    from src.integrations.mail.client import mail_client

    await backend_ws_client.close()
    await mail_client.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AGENT_PORT", 8000))
    uvicorn.run("agent.main:app", host="0.0.0.0", port=port, reload=True)
