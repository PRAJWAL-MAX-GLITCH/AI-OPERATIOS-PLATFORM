"""
Preprocessing Service
=====================
Orchestrates: load validated dataset → build config → run pipeline → persist report.
Enforces that ONLY validated datasets (quality_score not None) can be preprocessed.
"""
from __future__ import annotations
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.preprocessing import PreprocessingReport
from app.models.validation import ValidationReport
from app.services.dataset import dataset_service
from app.services.storage import storage_service
from app.services.dataset_parser import parse_file
from app.services.preprocessing.pipeline import run_preprocessing_pipeline
from app.services.preprocessing.config import (
    PipelineConfig, MissingConfig, EncodingConfig,
    ScalingConfig, TransformationConfig, GenerationConfig, SelectionConfig,
)
from app.services.preprocessing.serializer import save_pipeline
from app.schemas.preprocessing import PreprocessingRequest
from app.core.exceptions import ForbiddenError, ResourceNotFoundError

logger = structlog.get_logger(__name__)


class PreprocessingService:

    async def run_preprocessing(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
        request: PreprocessingRequest,
    ) -> PreprocessingReport:
        """
        Enforce validation gate → load dataset → run pipeline → persist report.
        """
        dataset = await dataset_service.get_dataset_or_404(db, dataset_id)

        # ── Validation Gate ───────────────────────────────────── #
        val_query = (
            select(ValidationReport)
            .where(
                ValidationReport.dataset_id == dataset_id,
                ValidationReport.status     == "completed",
                ValidationReport.is_active  == True,
            )
            .order_by(ValidationReport.created_at.desc())
            .limit(1)
        )
        val_result = await db.execute(val_query)
        val_report = val_result.scalars().first()
        if not val_report:
            raise ForbiddenError(
                "Dataset has not been validated. "
                "Run POST /datasets/{id}/validate before preprocessing."
            )

        # ── Build Config ─────────────────────────────────────── #
        cfg = PipelineConfig(
            mode=request.mode,
            target_column=request.target_column,
            drop_columns=request.drop_columns,
            missing=MissingConfig(strategy=request.missing_strategy),
            encoding=EncodingConfig(strategy=request.encoding_strategy),
            scaling=ScalingConfig(strategy=request.scaling_strategy),
            transformation=TransformationConfig(
                auto_transform_skewed=request.auto_transform_skewed,
            ),
            generation=GenerationConfig(polynomial_degree=request.polynomial_degree),
            selection=SelectionConfig(
                strategy=request.selection_strategy,
                target_column=request.target_column,
            ),
        )

        # ── Persist Initial Report ───────────────────────────── #
        report = PreprocessingReport(
            dataset_id=dataset.id,
            status="running",
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        logger.info("preprocessing_started", dataset_id=str(dataset_id), report_id=str(report.id))

        try:
            content = await storage_service.read(dataset.storage_path)
            df      = parse_file(content, dataset.original_filename)
            out_df, result = run_preprocessing_pipeline(df, cfg, dataset_name=dataset.name)

            # Save pipeline metadata
            pipeline_path = save_pipeline(
                result.to_dict(), str(dataset_id), cfg.model_dump()
            )

            report.status         = "completed"
            report.input_shape    = list(result.input_shape)
            report.output_shape   = list(result.output_shape)
            report.output_columns = result.output_columns
            report.pipeline_path  = pipeline_path
            report.report         = result.to_dict()

            logger.info(
                "preprocessing_completed",
                dataset_id=str(dataset_id),
                input=result.input_shape,
                output=result.output_shape,
            )
        except Exception as exc:
            report.status        = "failed"
            report.error_message = str(exc)
            logger.error("preprocessing_failed", dataset_id=str(dataset_id), error=str(exc))

        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    async def get_latest_report(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> PreprocessingReport:
        query = (
            select(PreprocessingReport)
            .where(
                PreprocessingReport.dataset_id == dataset_id,
                PreprocessingReport.status     == "completed",
                PreprocessingReport.is_active  == True,
            )
            .order_by(PreprocessingReport.created_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        report = result.scalars().first()
        if not report:
            raise ResourceNotFoundError(
                "No completed preprocessing report found. Run preprocessing first."
            )
        return report

    async def get_pipeline_history(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> list[PreprocessingReport]:
        query = (
            select(PreprocessingReport)
            .where(
                PreprocessingReport.dataset_id == dataset_id,
                PreprocessingReport.is_active  == True,
            )
            .order_by(PreprocessingReport.created_at.desc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())


preprocessing_service = PreprocessingService()
