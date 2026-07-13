"""
Enterprise Dataset Service
Orchestrates: upload → checksum dedup → storage → parse → profile → persist.
Follows the same Service/Repository/Schema pattern as the rest of the platform.
"""
import hashlib
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
import structlog
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, ResourceNotFoundError, ForbiddenError
from app.models.domain import Dataset, DatasetVersion, User
from app.repositories.dataset import dataset_repo
from app.services.storage import storage_service
from app.services.dataset_parser import parse_file, infer_schema, SUPPORTED_FORMATS
from app.services.dataset_profiler import generate_profile

logger = structlog.get_logger(__name__)
settings = get_settings()

BYTES_PER_MB = 1024 * 1024


class DatasetService:
    # ------------------------------------------------------------------ #
    # UPLOAD                                                               #
    # ------------------------------------------------------------------ #
    async def upload_dataset(
        self,
        db: AsyncSession,
        *,
        project_id: uuid.UUID,
        file: UploadFile,
        name: str,
        description: str | None,
        dataset_type: str,
        current_user: User,
    ) -> Dataset:
        content = await file.read()
        filename = file.filename or "upload"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        # ── Security Validations ──────────────────────────────────────── #
        if ext not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format '.{ext}'. Allowed: {', '.join(SUPPORTED_FORMATS)}")

        size_mb = len(content) / BYTES_PER_MB
        if size_mb > settings.DATASET_MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File too large ({size_mb:.1f} MB). Max allowed: {settings.DATASET_MAX_FILE_SIZE_MB} MB"
            )

        # ── Checksum & Dedup ─────────────────────────────────────────── #
        checksum = hashlib.sha256(content).hexdigest()
        existing = await dataset_repo.get_by_checksum_in_project(
            db, project_id=project_id, checksum=checksum
        )
        if existing:
            raise ConflictError(
                f"An identical file already exists in this project as '{existing.name}' (v{existing.version})."
            )

        # ── Persist Raw File ─────────────────────────────────────────── #
        relative_path = f"{project_id}/{uuid.uuid4()}/{filename}"
        storage_path = await storage_service.save(content, relative_path)

        # ── Parse & Profile ──────────────────────────────────────────── #
        df: pd.DataFrame | None = None
        schema_info: dict[str, Any] = {}
        profile: dict[str, Any] = {}
        row_count = column_count = None
        status = "processing"

        try:
            df = parse_file(content, filename)
            schema_info = infer_schema(df)
            profile = generate_profile(df, dataset_name=name)
            row_count = len(df)
            column_count = len(df.columns)
            status = "ready"
        except Exception as exc:
            logger.warning("dataset_parse_failed", filename=filename, error=str(exc))
            status = "error"

        # ── Persist Metadata ─────────────────────────────────────────── #
        db_dataset = Dataset(
            name=name,
            description=description,
            original_filename=filename,
            storage_path=storage_path,
            dataset_type=dataset_type,
            file_format=ext,
            file_size_bytes=len(content),
            checksum=checksum,
            version=1,
            row_count=row_count,
            column_count=column_count,
            status=status,
            profile=profile or None,
            schema_info=schema_info or None,
            project_id=project_id,
            created_by_id=current_user.id,
        )
        db.add(db_dataset)
        await db.commit()
        await db.refresh(db_dataset)

        # ── Initial Version Snapshot ─────────────────────────────────── #
        snapshot = DatasetVersion(
            dataset_id=db_dataset.id,
            version=1,
            storage_path=storage_path,
            original_filename=filename,
            checksum=checksum,
            file_size_bytes=len(content),
            row_count=row_count,
            column_count=column_count,
            notes="Initial upload",
        )
        db.add(snapshot)
        await db.commit()

        logger.info(
            "dataset_uploaded",
            dataset_id=str(db_dataset.id),
            project_id=str(project_id),
            rows=row_count,
            cols=column_count,
            status=status,
        )
        return db_dataset

    # ------------------------------------------------------------------ #
    # GET / VALIDATE                                                        #
    # ------------------------------------------------------------------ #
    async def get_dataset_or_404(self, db: AsyncSession, dataset_id: uuid.UUID) -> Dataset:
        dataset = await dataset_repo.get(db, id=dataset_id)
        if not dataset:
            raise ResourceNotFoundError("Dataset not found")
        return dataset

    def assert_project_ownership(self, dataset: Dataset, project_id: uuid.UUID) -> None:
        if dataset.project_id != project_id:
            raise ForbiddenError("Dataset does not belong to this project")

    # ------------------------------------------------------------------ #
    # PREVIEW                                                              #
    # ------------------------------------------------------------------ #
    async def get_preview(
        self, dataset: Dataset, *, page: int = 1, page_size: int = 100
    ) -> dict[str, Any]:
        content = await storage_service.read(dataset.storage_path)
        df = parse_file(content, dataset.original_filename)

        total = len(df)
        start = (page - 1) * page_size
        end = start + page_size
        page_df = df.iloc[start:end].fillna("")

        return {
            "columns": list(df.columns),
            "rows": page_df.to_dict(orient="records"),
            "total_rows": total,
            "page": page,
            "page_size": page_size,
        }

    # ------------------------------------------------------------------ #
    # VERSIONING / ROLLBACK                                                #
    # ------------------------------------------------------------------ #
    async def rollback(
        self, db: AsyncSession, dataset: Dataset, target_version: int
    ) -> Dataset:
        versions = await dataset_repo.get_versions(db, dataset_id=dataset.id)
        match = next((v for v in versions if v.version == target_version), None)
        if not match:
            raise ResourceNotFoundError(f"Version {target_version} not found")

        dataset.storage_path = match.storage_path
        dataset.original_filename = match.original_filename
        dataset.checksum = match.checksum
        dataset.file_size_bytes = match.file_size_bytes
        dataset.row_count = match.row_count
        dataset.column_count = match.column_count
        dataset.version = match.version

        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)

        logger.info("dataset_rollback", dataset_id=str(dataset.id), target_version=target_version)
        return dataset


dataset_service = DatasetService()
