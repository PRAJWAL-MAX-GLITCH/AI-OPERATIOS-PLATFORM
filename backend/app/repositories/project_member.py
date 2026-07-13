from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.repositories.base import CRUDBase
from app.models.domain import ProjectMember
from app.schemas.project import ProjectMemberCreate, ProjectMemberUpdate
from typing import Optional, List
import uuid

class ProjectMemberRepository(CRUDBase[ProjectMember, ProjectMemberCreate, ProjectMemberUpdate]):
    async def get_member(self, db: AsyncSession, *, project_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ProjectMember]:
        query = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_project_members(self, db: AsyncSession, *, project_id: uuid.UUID) -> List[ProjectMember]:
        query = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        )
        result = await db.execute(query)
        return list(result.scalars().all())

project_member_repo = ProjectMemberRepository(ProjectMember)
