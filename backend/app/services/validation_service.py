"""
Validation Service
==================
Orchestrates: load dataset → run pipeline → persist report.
Integrates with existing DatasetService and StorageService.
"""
from __future__ import annotations
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.validation import ValidationReport
from app.services.dataset import dataset_service
from app.services.storage import storage_service
from app.services.dataset_parser import parse_file
from app.services.validation.pipeline import run_validation_pipeline
from app.core.exceptions import ResourceNotFoundError

logger = structlog.get_logger(__name__)


class ValidationService:

    async def run_validation(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> ValidationReport:
        """
        Load the dataset file, run the full validation pipeline,
        persist the ValidationReport, and return it.
        """
        dataset = await dataset_service.get_dataset_or_404(db, dataset_id)

        # Mark existing report as superseded (soft approach: create new one)
        report = ValidationReport(
            dataset_id=dataset.id,
            status="running",
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        logger.info("validation_started", dataset_id=str(dataset.id), report_id=str(report.id))

        try:
            content = await storage_service.read(dataset.storage_path)
            df      = parse_file(content, dataset.original_filename)
            result  = run_validation_pipeline(df, dataset_name=dataset.name)

            report.status        = "completed"
            report.quality_score = result.quality_score.get("overall_score")
            report.grade         = result.quality_score.get("grade")
            report.report        = result.to_dict()

            logger.info(
                "validation_completed",
                dataset_id=str(dataset.id),
                report_id=str(report.id),
                score=report.quality_score,
                grade=report.grade,
            )
        except Exception as exc:
            report.status        = "failed"
            report.error_message = str(exc)
            logger.error("validation_failed", dataset_id=str(dataset.id), error=str(exc))

        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    async def get_latest_report(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> ValidationReport:
        query = (
            select(ValidationReport)
            .where(
                ValidationReport.dataset_id == dataset_id,
                ValidationReport.is_active  == True,
                ValidationReport.status     == "completed",
            )
            .order_by(ValidationReport.created_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        report = result.scalars().first()
        if not report:
            raise ResourceNotFoundError("No completed validation report found. Run validation first.")
        return report


validation_service = ValidationService()
