from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import structlog

from app.models.domain import User
from app.schemas.auth import LoginRequest, Token
from app.repositories.user import user_repo
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token
from app.core.exceptions import InvalidCredentialsError, UnauthorizedError

logger = structlog.get_logger(__name__)

class AuthService:
    async def authenticate(self, db: AsyncSession, login_data: LoginRequest) -> User:
        user = await user_repo.get_by_email(db, email=login_data.email)
        if not user:
            logger.warning("authentication_failed", reason="user_not_found", email=login_data.email)
            raise InvalidCredentialsError()

        if not verify_password(login_data.password, user.hashed_password):
            logger.warning("authentication_failed", reason="invalid_password", email=login_data.email)
            raise InvalidCredentialsError()

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        
        logger.info("user_authenticated", user_id=str(user.id))
        return user

    def generate_tokens(self, user: User) -> Token:
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def refresh_tokens(self, db: AsyncSession, refresh_token: str) -> Token:
        payload = verify_token(refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError(message="Invalid token payload")

        user = await user_repo.get(db, id=user_id)
        if not user:
            raise UnauthorizedError(message="User not found")

        logger.info("tokens_refreshed", user_id=str(user.id))
        return self.generate_tokens(user)

auth_service = AuthService()
