import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse

from backend.database import init_db, seed_data
from backend.routes.auth import router as auth_router
from backend.routes.email import router as email_router
from backend.routes.ws_notifications import router as ws_router, connection_manager

AGENT_BASE_URL = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:8000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_data()
    yield
    await connection_manager.shutdown()


app = FastAPI(
    title="Email Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

static_dir = os.path.join(os.path.dirname(__file__), "static")


@app.get("/static/{filename:path}")
async def serve_static(filename: str):
    file_path = os.path.join(static_dir, filename.split("?")[0])
    if not os.path.isfile(file_path):
        return Response(status_code=404)
    return FileResponse(
        file_path,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(email_router, prefix="/api/emails", tags=["emails"])
app.include_router(ws_router, tags=["websocket"])


@app.get("/api/agent/health")
async def check_agent_health():
    try:
        from httpx import AsyncClient

        async with AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{AGENT_BASE_URL}/health")
            if response.status_code == 200:
                return {"status": "online"}
            return {"status": "offline"}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


@app.api_route(
    "/api/agent/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_to_agent(path: str, request: Request):
    url = f"{AGENT_BASE_URL}/api/agent/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        from httpx import AsyncClient, ConnectError, ReadTimeout

        try:
            async with AsyncClient(timeout=120.0) as client:
                body = await request.body()
                response = await client.request(
                    method=request.method,
                    url=url,
                    content=body,
                    headers=headers,
                    params=request.query_params,
                )
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
        except (ConnectError, ReadTimeout) as e:
            return JSONResponse(
                status_code=502,
                content={"error": f"Cannot connect to Agent backend: {str(e)}"},
            )
    except Exception as e:
        print(f"Proxy error: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": f"Agent backend error: {str(e)}"},
        )


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/")
async def serve_index():
    return FileResponse(
        os.path.join(static_dir, "index.html"),
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("EMAIL_BACKEND_PORT", 5001))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
