from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.exceptions import AppException, app_exception_handler, global_exception_handler
from app.api.v1.router import api_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    configure_logging()
    logger = structlog.get_logger(__name__)
    logger.info("startup.complete", env=settings.APP_ENV, project=settings.PROJECT_NAME)
    yield
    # Shutdown actions
    logger.info("shutdown.complete")

def create_app() -> FastAPI:
    """
    Application factory pattern.
    Allows for easy testing and configuration injection.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan
    )

    # Middlewares (Order matters: outermost first)
    app.add_middleware(RequestContextMiddleware)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler) # type: ignore
    app.add_exception_handler(Exception, global_exception_handler)

    # Routers
    app.include_router(api_router, prefix=settings.API_PREFIX)

    @app.get("/", tags=["root"])
    async def root():
        return {"message": "Welcome to the Enterprise AI Operations Platform API"}

    return app

app = create_app()
