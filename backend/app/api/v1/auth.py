from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.responses import ApiResponse
from app.schemas.auth import LoginRequest, Token, RefreshRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import auth_service
from app.services.user import user_service
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/register", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> ApiResponse[UserResponse]:
    """Register a new user."""
    user = await user_service.create_user(db, user_in=user_in)
    return ApiResponse(data=UserResponse.model_validate(user))

@router.post("/login", response_model=ApiResponse[Token])
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)) -> ApiResponse[Token]:
    """Authenticate and receive access and refresh tokens."""
    user = await auth_service.authenticate(db, login_data=login_data)
    tokens = auth_service.generate_tokens(user)
    return ApiResponse(data=tokens)

@router.post("/refresh", response_model=ApiResponse[Token])
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)) -> ApiResponse[Token]:
    """Refresh access token using a valid refresh token."""
    tokens = await auth_service.refresh_tokens(db, refresh_token=request.refresh_token)
    return ApiResponse(data=tokens)
