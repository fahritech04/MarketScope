from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnalysisCreate(BaseModel):
    topic: str = Field(min_length=3, max_length=200)
    location: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=120)


class AnalysisResponse(BaseModel):
    id: str
    topic: str
    location: str | None
    category: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    sources_count: int | None = None
    items_count: int | None = None


class SourceResponse(BaseModel):
    id: str
    analysis_id: str
    url: str
    title: str | None
    source_type: str
    status: str
    created_at: datetime


class ScrapedItemResponse(BaseModel):
    id: str
    analysis_id: str
    source_id: str | None
    name: str | None
    description: str | None
    address: str | None
    price_text: str | None
    price_min: float | None
    price_max: float | None
    rating: float | None
    review_count: int | None
    raw_text: str | None
    metadata: dict[str, Any] | None
    created_at: datetime


class InsightResponse(BaseModel):
    id: str
    analysis_id: str
    summary: str | None
    opportunities: list[str]
    competitors: list[str]
    pricing_insight: str | None
    customer_pain_points: list[str]
    strategy_recommendations: list[str]
    raw_ai_response: dict[str, Any]
    created_at: datetime

