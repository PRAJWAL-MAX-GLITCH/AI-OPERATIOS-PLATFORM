import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

logger = structlog.get_logger(__name__)

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject correlation IDs and log request timing.
    This is essential for tracing requests across microservices and async boundaries.
    """
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        bind_contextvars(request_id=request_id, method=request.method, path=request.url.path)
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            logger.info("request_completed", status_code=response.status_code, process_time_ms=round(process_time * 1000, 2))
            
            return response
        except Exception as e:
            process_time = time.perf_counter() - start_time
            logger.error("request_failed", exc_info=e, process_time_ms=round(process_time * 1000, 2))
            raise
