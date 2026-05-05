import os
import asyncio
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from agent.routes.agent import (
    CreateThreadRequest,
    CreateDraftRequest,
    DraftReplyRequest,
    create_thread,
    create_draft,
    get_thread,
    cancel_thread,
    reply_to_draft,
    get_user_threads,
    confirm_meeting,
    decline_meeting,
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


@app.post("/api/agent/thread")
async def agent_create_thread(request: CreateThreadRequest):
    return await create_thread(request)


@app.post("/api/agent/draft")
async def agent_create_draft(request: CreateDraftRequest):
    return await create_draft(request)


@app.get("/api/agent/thread/{thread_id}")
async def agent_get_thread(thread_id: str):
    return await get_thread(thread_id)


@app.delete("/api/agent/thread/{thread_id}")
async def agent_cancel_thread(thread_id: str):
    return await cancel_thread(thread_id)


@app.post("/api/agent/thread/{thread_id}/reply")
async def agent_reply_to_thread(thread_id: str, request: DraftReplyRequest):
    return await reply_to_draft(thread_id, request)


@app.get("/api/agent/threads")
async def agent_list_threads(user_id: int, status: Optional[str] = None):
    return await get_user_threads(user_id, status)


@app.post("/api/agent/thread/{thread_id}/confirm")
async def agent_confirm_meeting(thread_id: str):
    return await confirm_meeting(thread_id)


@app.post("/api/agent/thread/{thread_id}/decline")
async def agent_decline_meeting(thread_id: str):
    return await decline_meeting(thread_id)


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
