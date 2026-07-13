from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.repositories.base import CRUDBase
from app.models.domain import Project, ProjectMember
from app.schemas.project import ProjectCreate, ProjectUpdate
from typing import Optional, List
import uuid

class ProjectRepository(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    async def get_by_name_and_owner(self, db: AsyncSession, *, name: str, owner_id: uuid.UUID) -> Optional[Project]:
        query = select(Project).where(
            Project.name == name,
            Project.owner_id == owner_id,
            Project.is_active == True
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_user_projects(self, db: AsyncSession, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        Gets projects where the user is either the owner OR a member.
        """
        query = (
            select(Project)
            .outerjoin(ProjectMember)
            .where(
                and_(
                    Project.is_active == True,
                    or_(
                        Project.owner_id == user_id,
                        and_(ProjectMember.user_id == user_id, ProjectMember.is_active == True)
                    )
                )
            )
            .distinct()
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

project_repo = ProjectRepository(Project)
