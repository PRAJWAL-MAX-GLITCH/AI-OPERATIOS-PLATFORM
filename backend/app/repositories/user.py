from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import CRUDBase
from app.models.domain import User
from app.schemas.user import UserCreate, UserUpdate
from typing import Optional
import uuid

class UserRepository(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        query = select(User).where(User.email == email, User.is_active == True)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        query = select(User).where(User.username == username, User.is_active == True)
        result = await db.execute(query)
        return result.scalars().first()

user_repo = UserRepository(User)
