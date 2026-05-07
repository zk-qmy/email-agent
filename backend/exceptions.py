import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Any

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_id: str = None):
        self.message = message
        self.status_code = status_code
        self.error_id = error_id or str(uuid.uuid4())[:8]
        super().__init__(self.message)


def error_to_dict(e: Exception, error_id: str) -> dict[str, Any]:
    result = {
        "error": type(e).__name__,
        "error_id": error_id,
    }
    if isinstance(e, AppError):
        result["message"] = e.message
    elif isinstance(e, ValueError):
        result["message"] = str(e)
    else:
        result["message"] = "An unexpected error occurred"
        result["detail"] = str(e)
    return result


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        error_id = str(uuid.uuid4())[:8]
        
        try:
            return await call_next(request)
        except AppError as e:
            logger.warning(f"[{error_id}] AppError: {e.message}")
            return JSONResponse(
                status_code=e.status_code,
                content=error_to_dict(e, error_id),
            )
        except Exception as e:
            logger.exception(f"[{error_id}] Unhandled exception: {e}")
            return JSONResponse(
                status_code=500,
                content=error_to_dict(e, error_id),
            )


def add_exception_handlers(app: FastAPI):
    app.add_middleware(GlobalExceptionMiddleware)