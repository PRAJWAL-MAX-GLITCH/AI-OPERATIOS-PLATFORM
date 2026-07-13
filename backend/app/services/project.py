from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project import project_repo
from app.repositories.project_member import project_member_repo
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberCreate
from app.models.domain import Project, ProjectMember, User
from app.core.exceptions import ConflictError, ProjectNotFoundError, ForbiddenError, InvalidProjectMemberError
import structlog
import uuid

logger = structlog.get_logger(__name__)

class ProjectService:
    async def create_project(self, db: AsyncSession, project_in: ProjectCreate, owner: User) -> Project:
        # Check duplicate name for this owner
        existing = await project_repo.get_by_name_and_owner(db, name=project_in.name, owner_id=owner.id)
        if existing:
            raise ConflictError("A project with this name already exists for this user.")

        # Create project
        db_project = Project(
            name=project_in.name,
            description=project_in.description,
            visibility=project_in.visibility,
            tags=project_in.tags,
            owner_id=owner.id
        )
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        
        # Add owner to ProjectMember with 'owner' role
        member = ProjectMember(
            project_id=db_project.id,
            user_id=owner.id,
            role="owner"
        )
        db.add(member)
        await db.commit()

        logger.info("project_created", project_id=str(db_project.id), owner_id=str(owner.id))
        return db_project
        
    async def get_project_or_404(self, db: AsyncSession, project_id: uuid.UUID) -> Project:
        project = await project_repo.get(db, id=project_id)
        if not project:
            raise ProjectNotFoundError()
        return project

    async def add_member(self, db: AsyncSession, project_id: uuid.UUID, member_in: ProjectMemberCreate) -> ProjectMember:
        project = await self.get_project_or_404(db, project_id)
        
        existing_member = await project_member_repo.get_member(db, project_id=project_id, user_id=member_in.user_id)
        if existing_member:
            raise ConflictError("User is already a member of this project.")
            
        new_member = ProjectMember(
            project_id=project.id,
            user_id=member_in.user_id,
            role=member_in.role
        )
        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)
        
        logger.info("project_member_added", project_id=str(project.id), user_id=str(member_in.user_id), role=member_in.role)
        return new_member

    async def remove_member(self, db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        member = await project_member_repo.get_member(db, project_id=project_id, user_id=user_id)
        if not member:
            raise InvalidProjectMemberError("Member not found in project.")
            
        if member.role == "owner":
            raise ForbiddenError("Cannot remove the project owner. Transfer ownership first.")
            
        await project_member_repo.remove(db, id=member.id)
        logger.info("project_member_removed", project_id=str(project_id), user_id=str(user_id))

project_service = ProjectService()
