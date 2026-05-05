from pydantic import BaseModel
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from agent.services.agent_service import agent_service


class CreateThreadRequest(BaseModel):
    user_id: int


class CreateDraftRequest(BaseModel):
    user_id: int
    prompt: str
    thread_id: Optional[str] = None


class DraftReplyRequest(BaseModel):
    user_id: int
    response: str


async def create_thread(request: CreateThreadRequest):
    try:
        result = agent_service.create_empty_thread(user_id=request.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")


async def create_draft(request: CreateDraftRequest):
    try:
        result = await agent_service.create_draft_async(
            user_id=request.user_id,
            prompt=request.prompt,
            thread_id=request.thread_id,
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create draft: {str(e)}")


async def get_thread(thread_id: str):
    try:
        result = agent_service.get_draft(thread_id)
        if not result:
            raise HTTPException(status_code=404, detail="Thread not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thread: {str(e)}")





async def cancel_thread(thread_id: str):
    try:
        result = agent_service.cancel_draft(thread_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove thread: {str(e)}")


async def reply_to_draft(thread_id: str, request: DraftReplyRequest):
    try:
        result = await agent_service.reply_to_draft_async(
            thread_id=thread_id,
            user_id=request.user_id,
            response=request.response,
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reply to thread: {str(e)}")


async def get_user_drafts(user_id: int, status: Optional[str] = None):
    result = agent_service.get_user_drafts(user_id, status)
    return {"drafts": result}


async def get_thread(thread_id: str):
    try:
        result = agent_service.get_thread(thread_id)
        if not result:
            raise HTTPException(status_code=404, detail="Thread not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thread: {str(e)}")


async def get_user_threads(user_id: int, status: Optional[str] = None):
    result = agent_service.get_user_threads(user_id, status)
    return {"threads": result}


async def confirm_meeting(thread_id: str):
    try:
        result = await agent_service.confirm_meeting(thread_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to confirm meeting: {str(e)}"
        )


async def decline_meeting(thread_id: str):
    try:
        result = await agent_service.decline_meeting(thread_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to decline meeting: {str(e)}"
        )


async def get_status(thread_id: str):
    try:
        result = agent_service.get_status(thread_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


async def get_history(thread_id: str):
    try:
        result = agent_service.get_history(thread_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


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
                        await websocket.send_json(
                            {
                                "event": "status",
                                "thread_id": thread_id,
                                "status": thread["status"],
                                "reply_intent": thread["reply_intent"],
                            }
                        )

            elif event == "subscribe":
                thread_id = data.get("thread_id")
                await websocket.send_json(
                    {
                        "event": "subscribed",
                        "thread_id": thread_id,
                    }
                )

    except WebSocketDisconnect:
        agent_service.remove_websocket(user_id, websocket)
    except Exception as e:
        await websocket.send_json({"event": "error", "message": str(e)})
        agent_service.remove_websocket(user_id, websocket)
