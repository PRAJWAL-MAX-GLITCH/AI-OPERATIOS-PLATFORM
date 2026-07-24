from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import structlog
import uuid

from app.core.database import get_db_session
from app.core.security import verify_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.models.domain import User
from app.repositories.user import user_repo
from app.repositories.project_member import project_member_repo

logger = structlog.get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db(session: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    return session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = verify_token(token, token_type="access")
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError(message="Invalid token payload")
        
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError(message="Invalid token payload format")

    user = await user_repo.get(db, id=user_id)
    if not user or not user.is_active:
        raise UnauthorizedError(message="User not found or inactive")
    return user

class RequireRole:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenError(message="You do not have permission to perform this action.")
        return current_user

class RequireProjectRole:
    """
    Project-level RBAC. Extracts project_id from the route path kwargs and validates
    that the current user has the required project role in the ProjectMember table.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self, 
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # Extract project_id from path parameters
        project_id_str = request.path_params.get("id") or request.path_params.get("project_id")
        if not project_id_str:
            raise ForbiddenError("Project ID missing from request path")
            
        try:
            project_id = uuid.UUID(project_id_str)
        except ValueError:
            raise ForbiddenError("Invalid Project ID format")

        member = await project_member_repo.get_member(db, project_id=project_id, user_id=current_user.id)
        
        # System admins can bypass project roles
        if current_user.role == "admin":
            return current_user
            
        if not member or member.role not in self.allowed_roles:
            logger.warning("unauthorized_project_access", user_id=str(current_user.id), project_id=str(project_id), required=self.allowed_roles)
            raise ForbiddenError(message=f"You do not have the required project role. Allowed: {', '.join(self.allowed_roles)}")
            
        return current_user
