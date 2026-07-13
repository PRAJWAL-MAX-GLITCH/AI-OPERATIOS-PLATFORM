import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Any

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy declarative models.
    """
    id: Any
    __name__: str
    
    # Common audit timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Soft delete flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UUIDBaseModel(Base):
    """
    Abstract base model that sets the primary key to a UUID.
    This is best practice for enterprise systems to avoid integer ID enumeration attacks
    and to allow distributed systems to generate IDs without database collisions.
    """
    __abstract__ = True
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
