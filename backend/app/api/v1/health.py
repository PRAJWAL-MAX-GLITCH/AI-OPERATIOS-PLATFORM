from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas.responses import ApiResponse
from app.api.dependencies import get_db

router = APIRouter()

@router.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check(db: AsyncSession = Depends(get_db)) -> ApiResponse[dict[str, str]]:
    """
    Enhanced health check endpoint.
    Verifies that the API is running AND that the database is reachable.
    """
    db_status = "unhealthy"
    try:
        # Perform a lightweight ping to verify connection pooling works
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return ApiResponse(
        data={
            "status": "ok", 
            "service": "enterprise-ai-backend",
            "database": db_status
        }
    )
