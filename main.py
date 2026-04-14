# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.app.api.routes import router
import src.workflows.registry as reg


@asynccontextmanager
async def lifespan(app: FastAPI):
    await reg.startup()   # compile all graphs async
    yield

app = FastAPI(title="Email Agent", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
