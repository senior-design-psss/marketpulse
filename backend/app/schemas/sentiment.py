"""Pydantic schemas for sentiment feed endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class SentimentFeedItem(BaseModel):
    id: uuid.UUID
    source: str
    company_symbol: str | None = None
    company_name: str | None = None
    title: str | None = None
    body_excerpt: str
    ensemble_score: float
    ensemble_label: str
    ensemble_confidence: float
    finbert_label: str | None = None
    llm_reasoning: str | None = None
    scored_at: datetime


class SentimentFeedResponse(BaseModel):
    items: list[SentimentFeedItem]
    total: int
    page: int
    page_size: int


class MarketOverview(BaseModel):
    overall_score: float
    overall_label: str
    total_items_today: int
    active_alerts: int
    sources_active: int
    industries: list[dict]
