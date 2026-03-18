import os
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import init_db, seed_data
from backend.routes.auth import router as auth_router
from backend.routes.email import router as email_router
from backend.routes.ws_notifications import router as ws_router, connection_manager


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


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("EMAIL_BACKEND_PORT", 5001))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
