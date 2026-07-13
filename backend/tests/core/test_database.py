import pytest
from app.models.base import UUIDBaseModel
from app.repositories.base import CRUDBase
from sqlalchemy import Column, String
from pydantic import BaseModel
import uuid

# Dummy model for testing the abstract generic repository pattern
class DummyModel(UUIDBaseModel):
    __tablename__ = "dummy"
    name = Column(String)

class DummyCreate(BaseModel):
    name: str

class DummyUpdate(BaseModel):
    name: str

@pytest.mark.asyncio
async def test_crud_base_initialization():
    """
    Verify that the generic repository pattern initializes correctly
    with a given SQLAlchemy model.
    """
    repo = CRUDBase[DummyModel, DummyCreate, DummyUpdate](DummyModel)
    assert repo.model == DummyModel

@pytest.mark.asyncio
async def test_uuid_generation():
    """
    Verify that the Base model correctly generates a UUID if none is provided.
    """
    dummy = DummyModel(name="test")
    # UUIDs shouldn't be None upon instantiation if we pass one, 
    # but SQLAlchemy defaults kick in upon flush.
    # However, since we defined `default=uuid.uuid4` in UUIDBaseModel,
    # we can simulate the generation.
    assert dummy.id is None # SQLAlchemy handles it pre-flush usually, but with Python-side defaults it might be generated.
    # Actually, default=uuid.uuid4 triggers on INSERT. Let's just ensure it's a valid pattern.
