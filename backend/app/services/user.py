from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import user_repo
from app.schemas.user import UserCreate, UserUpdate
from app.models.domain import User
from app.core.security import get_password_hash
from app.core.exceptions import ConflictError
from typing import Optional
import uuid
import structlog

logger = structlog.get_logger(__name__)

class UserService:
    async def get_user_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        return await user_repo.get(db, id=user_id)

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        user_by_email = await user_repo.get_by_email(db, email=user_in.email)
        if user_by_email:
            logger.warning("user_creation_failed", reason="email_exists", email=user_in.email)
            raise ConflictError(message="Email already registered")

        user_by_username = await user_repo.get_by_username(db, username=user_in.username)
        if user_by_username:
            logger.warning("user_creation_failed", reason="username_exists", username=user_in.username)
            raise ConflictError(message="Username already taken")

        # Hash password before storing
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=hashed_password,
            role="viewer"  # Default role
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        logger.info("user_created", user_id=str(db_user.id), email=db_user.email)
        return db_user

user_service = UserService()
