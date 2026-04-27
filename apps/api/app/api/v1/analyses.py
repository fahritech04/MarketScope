from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.v1.dependencies import get_repository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.local_analysis_repository import LocalAnalysisRepository
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisResponse,
    InsightResponse,
    ScrapedItemResponse,
    SourceResponse,
)
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
def create_analysis(
    payload: AnalysisCreate, repository: AnalysisRepository | LocalAnalysisRepository = Depends(get_repository)
) -> AnalysisResponse:
    created = repository.create_analysis(
        {
            "topic": payload.topic.strip(),
            "location": payload.location.strip() if payload.location else None,
            "category": payload.category.strip() if payload.category else None,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
    )
    return AnalysisResponse(**created, sources_count=0, items_count=0)


@router.get("", response_model=list[AnalysisResponse])
def list_analyses(
    repository: AnalysisRepository | LocalAnalysisRepository = Depends(get_repository),
) -> list[AnalysisResponse]:
    analyses = repository.list_analyses()
    result: list[AnalysisResponse] = []
    for analysis in analyses:
        result.append(
            AnalysisResponse(
                **analysis,
                sources_count=repository.count_sources(analysis["id"]),
                items_count=repository.count_items(analysis["id"]),
            )
        )
    return result


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str, repository: AnalysisRepository | LocalAnalysisRepository = Depends(get_repository)
) -> AnalysisResponse:
    analysis = repository.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis tidak ditemukan.")
    return AnalysisResponse(
        **analysis,
        sources_count=repository.count_sources(analysis_id),
        items_count=repository.count_items(analysis_id),
    )


@router.post("/{analysis_id}/run", status_code=status.HTTP_202_ACCEPTED)
def run_analysis(
    analysis_id: str,
    background_tasks: BackgroundTasks,
    repository: AnalysisRepository | LocalAnalysisRepository = Depends(get_repository),
) -> dict[str, str]:
    analysis = repository.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis tidak ditemukan.")

    if analysis["status"] in {"crawling", "scraping", "analyzing"}:
        return {"message": "Analisis sedang diproses."}

    service = PipelineService(repository)
    background_tasks.add_task(service.run_analysis, analysis_id)
    repository.update_analysis_status(analysis_id, "crawling")
    return {"message": "Proses analisis dimulai."}


@router.get("/{analysis_id}/sources", response_model=list[SourceResponse])
def get_sources(
    analysis_id: str, repository: AnalysisRepository | LocalAnalysisRepository = Depends(get_repository)
) -> list[SourceResponse]:
    if not repository.get_analysis(analysis_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis tidak ditemukan.")
    return [SourceResponse(**item) for item in repository.list_sources(analysis_id)]


@router.get("/{analysis_id}/items", response_model=list[ScrapedItemResponse])
def get_items(
    analysis_id: str, repository: AnalysisRepository | LocalAnalysisRepository = Depends(get_repository)
) -> list[ScrapedItemResponse]:
    if not repository.get_analysis(analysis_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis tidak ditemukan.")
    return [ScrapedItemResponse(**item) for item in repository.list_scraped_items(analysis_id)]


@router.get("/{analysis_id}/insights", response_model=InsightResponse)
def get_insight(
    analysis_id: str, repository: AnalysisRepository | LocalAnalysisRepository = Depends(get_repository)
) -> InsightResponse:
    if not repository.get_analysis(analysis_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis tidak ditemukan.")

    insight = repository.get_insight(analysis_id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight belum tersedia untuk analisis ini.",
        )
    return InsightResponse(**insight)
