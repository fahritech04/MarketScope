from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, status

from app.api.v1.dependencies import get_repository
from app.core.config import get_settings
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.local_analysis_repository import LocalAnalysisRepository
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/run-scheduler", status_code=status.HTTP_202_ACCEPTED)
def run_scheduler(
    background_tasks: BackgroundTasks,
    limit: int | None = Query(default=None, ge=1, le=20),
    include_failed: bool = Query(default=False),
    x_scheduler_token: str | None = Header(default=None),
    repository: AnalysisRepository | LocalAnalysisRepository = Depends(get_repository),
) -> dict[str, object]:
    settings = get_settings()
    effective_limit = limit or settings.scheduler_default_limit

    if settings.scheduler_auth_token:
        if not x_scheduler_token or x_scheduler_token != settings.scheduler_auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Scheduler token tidak valid.",
            )

    target_statuses = ["pending"]
    if include_failed:
        target_statuses.append("failed")

    queued = repository.list_analyses_by_status(statuses=target_statuses, limit=effective_limit)
    service = PipelineService(repository)
    dispatched_ids: list[str] = []

    for analysis in queued:
        analysis_id = analysis["id"]
        repository.update_analysis_status(analysis_id, "crawling")
        background_tasks.add_task(service.run_analysis, analysis_id)
        dispatched_ids.append(analysis_id)

    return {
        "message": "Scheduler dijalankan.",
        "requested_statuses": target_statuses,
        "effective_limit": effective_limit,
        "dispatched_count": len(dispatched_ids),
        "analysis_ids": dispatched_ids,
    }
