from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)

class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

class ResourceNotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(code="RESOURCE_NOT_FOUND", message=message, status_code=404)

class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized", code: str = "UNAUTHORIZED"):
        super().__init__(code=code, message=message, status_code=401)

class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)

class InvalidCredentialsError(AppException):
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(code="INVALID_CREDENTIALS", message=message, status_code=401)

class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(code="CONFLICT", message=message, status_code=409)

class ProjectNotFoundError(ResourceNotFoundError):
    def __init__(self, message: str = "Project not found"):
        super().__init__(message=message)

class InvalidProjectMemberError(AppException):
    def __init__(self, message: str = "Invalid project member"):
        super().__init__(code="INVALID_MEMBER", message=message, status_code=400)

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.error("app_exception", code=exc.code, message=exc.message, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", path=request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}},
    )
