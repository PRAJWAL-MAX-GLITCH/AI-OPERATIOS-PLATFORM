from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.responses import ApiResponse
from app.schemas.user import UserResponse
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user

router = APIRouter()

@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_my_profile(
    current_user: User = Depends(get_current_user)
) -> ApiResponse[UserResponse]:
    """
    Get the currently authenticated user's profile.
    Demonstrates the usage of the get_current_user dependency.
    """
    return ApiResponse(data=UserResponse.model_validate(current_user))
