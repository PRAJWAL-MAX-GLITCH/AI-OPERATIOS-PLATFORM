"""
Enterprise Storage Service
Provides an abstract interface that supports local filesystem now
and is designed to be swapped to S3/Azure Blob/GCS in production
without changing any calling code.
"""
import abc
import aiofiles
import os
from pathlib import Path
from app.core.config import get_settings

settings = get_settings()


class StorageService(abc.ABC):
    """Abstract base class for storage backends."""

    @abc.abstractmethod
    async def save(self, content: bytes, relative_path: str) -> str:
        """Persist content. Returns the canonical storage path."""
        ...

    @abc.abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """Read content from a storage path."""
        ...

    @abc.abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Delete content at storage path."""
        ...

    @abc.abstractmethod
    def get_absolute_path(self, storage_path: str) -> str:
        """Resolve a storage_path to an absolute filesystem/S3 URI."""
        ...


class LocalFileSystemStorage(StorageService):
    """
    Local disk storage backend.
    In development, stores under DATASET_STORAGE_ROOT.
    In production, swap this for S3Storage without touching the callers.
    """
    def __init__(self):
        self.root = Path(settings.DATASET_STORAGE_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)

    async def save(self, content: bytes, relative_path: str) -> str:
        destination = self.root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(destination, "wb") as f:
            await f.write(content)
        return str(destination)

    async def read(self, storage_path: str) -> bytes:
        async with aiofiles.open(storage_path, "rb") as f:
            return await f.read()

    async def delete(self, storage_path: str) -> None:
        path = Path(storage_path)
        if path.exists():
            path.unlink()

    def get_absolute_path(self, storage_path: str) -> str:
        return str(Path(storage_path).resolve())


def get_storage_service() -> StorageService:
    """Factory: returns the configured storage backend."""
    backend = settings.DATASET_STORAGE_BACKEND
    if backend == "local":
        return LocalFileSystemStorage()
    # Future: elif backend == "s3": return S3Storage()
    raise ValueError(f"Unsupported storage backend: {backend}")


# Singleton for the application
storage_service = get_storage_service()
