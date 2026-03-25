"""Pydantic schemas for company endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class CompanyBase(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str


class CompanyWithSentiment(CompanyBase):
    avg_score: float | None = None
    volume: int = 0
    momentum: float | None = None
    acceleration: float | None = None
    confidence: float | None = None
    industries: list[str] = []
    # Price data
    price: float | None = None
    price_change: float | None = None  # daily return as percentage
    price_date: str | None = None


class CompanyListResponse(BaseModel):
    companies: list[CompanyWithSentiment]


class CompanyDetail(CompanyWithSentiment):
    reddit_avg: float | None = None
    reddit_volume: int = 0
    news_avg: float | None = None
    news_volume: int = 0
    stocktwits_avg: float | None = None
    stocktwits_volume: int = 0


class TimeseriesPoint(BaseModel):
    timestamp: datetime
    score: float
    volume: int
    source: str | None = None


class CompanyTimeseriesResponse(BaseModel):
    company: CompanyBase
    data: list[TimeseriesPoint]
    timeframe: str
