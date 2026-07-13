from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import CRUDBase
from app.models.domain import Dataset, DatasetVersion
from app.schemas.dataset import DatasetUpdate
from typing import Optional, List
import uuid
from pydantic import BaseModel


class _DummyCreate(BaseModel):
    pass


class DatasetRepository(CRUDBase[Dataset, _DummyCreate, DatasetUpdate]):
    async def get_by_project(
        self, db: AsyncSession, *, project_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Dataset]:
        query = (
            select(Dataset)
            .where(Dataset.project_id == project_id, Dataset.is_active == True)
            .order_by(Dataset.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_checksum_in_project(
        self, db: AsyncSession, *, project_id: uuid.UUID, checksum: str
    ) -> Optional[Dataset]:
        query = select(Dataset).where(
            Dataset.project_id == project_id,
            Dataset.checksum == checksum,
            Dataset.is_active == True,
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_versions(
        self, db: AsyncSession, *, dataset_id: uuid.UUID
    ) -> List[DatasetVersion]:
        query = (
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version.desc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())


dataset_repo = DatasetRepository(Dataset)
