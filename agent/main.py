import logging
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from backend.exceptions import add_exception_handlers
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
from agent.routes.pdf import (
    ValidatePdfRequest,
    parse_pdf_file,
    validate_pdf_content,
    validate_pdf_upload,
)
from agent.routes.rag import (
    SuggestDepartmentRequest,
    AskGuideRequest,
    SearchRequest,
    handle_suggest_department,
    handle_ask_guide,
    handle_search,
    handle_rag_status,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from agent.services.ws_client import backend_ws_client
    from agent.services.agent_service import agent_service

    backend_ws_client.set_push_handler(agent_service.handle_backend_push)
    backend_ws_client._running = True

    yield

    await backend_ws_client.close()
    from src.integrations.mail.client import mail_client
    await mail_client.close()


app = FastAPI(title="Email Agent API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_exception_handlers(app)


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


@app.post("/api/agent/pdf/parse")
async def agent_parse_pdf(file: UploadFile = File(...)):
    return await parse_pdf_file(file)


@app.post("/api/agent/pdf/validate")
async def agent_validate_pdf(request: ValidatePdfRequest):
    return await validate_pdf_content(request)


@app.post("/api/agent/pdf/validate-upload")
async def agent_validate_pdf_upload(
    file: UploadFile = File(...),
    user_role: str = Form(...),
):
    return await validate_pdf_upload(file=file, user_role=user_role)


@app.post("/api/agent/rag/suggest-department")
async def agent_suggest_department(request: SuggestDepartmentRequest):
    return await handle_suggest_department(request)


@app.post("/api/agent/rag/ask-guide")
async def agent_ask_guide(request: AskGuideRequest):
    return await handle_ask_guide(request)


@app.post("/api/agent/rag/search")
async def agent_rag_search(request: SearchRequest):
    return await handle_search(request)


@app.get("/api/agent/rag/status")
async def agent_rag_status():
    return await handle_rag_status()


@app.websocket("/api/agent/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int):
    await websocket_endpoint(websocket, user_id)


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("AGENT_PORT", 8000))
    uvicorn.run("agent.main:app", host="0.0.0.0", port=port, reload=True)
