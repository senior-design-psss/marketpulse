"""Pydantic schemas for analyst endpoints."""

from datetime import datetime

from pydantic import BaseModel


class BriefingItem(BaseModel):
    id: str
    briefing_type: str
    title: str
    content: str
    key_insights: dict | None = None
    risk_factors: dict | None = None
    items_analyzed: int | None = None
    generated_at: datetime


class BriefingResponse(BaseModel):
    briefing: BriefingItem | None = None


class BriefingListResponse(BaseModel):
    briefings: list[BriefingItem]


class CompanySummaryResponse(BaseModel):
    symbol: str
    summary: str
    generated_at: datetime | None = None
