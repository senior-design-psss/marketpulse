"""Pydantic schemas for industry endpoints."""

import uuid

from pydantic import BaseModel


class IndustryBase(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    display_color: str | None = None


class IndustryWithSentiment(IndustryBase):
    avg_score: float | None = None
    volume: int = 0
    momentum: float | None = None
    confidence: float | None = None


class IndustryListResponse(BaseModel):
    industries: list[IndustryWithSentiment]


class HeatmapCompany(BaseModel):
    symbol: str
    name: str
    score: float
    volume: int
    momentum: float | None = None
    change: float | None = None  # Score change from last period


class HeatmapResponse(BaseModel):
    industry: IndustryBase
    companies: list[HeatmapCompany]


class RadarSource(BaseModel):
    reddit: float | None = None
    news: float | None = None
    stocktwits: float | None = None


class RadarCompany(BaseModel):
    symbol: str
    name: str
    sources: RadarSource


class RadarResponse(BaseModel):
    industry: IndustryBase
    companies: list[RadarCompany]
