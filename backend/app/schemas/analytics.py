"""Pydantic schemas for analytics endpoints."""

from datetime import datetime

from pydantic import BaseModel


class MomentumItem(BaseModel):
    symbol: str
    name: str
    avg_score: float
    momentum: float
    acceleration: float | None = None
    volume: int


class MomentumResponse(BaseModel):
    movers: list[MomentumItem]


class AnomalyAlertItem(BaseModel):
    id: str
    company_symbol: str | None = None
    alert_type: str
    severity: str
    title: str
    description: str
    metric_value: float | None = None
    baseline_value: float | None = None
    z_score: float | None = None
    triggered_at: datetime


class AnomalyResponse(BaseModel):
    alerts: list[AnomalyAlertItem]


class CrossSourceItem(BaseModel):
    symbol: str
    source_a: str
    source_b: str
    score_a: float
    score_b: float
    divergence: float


class CrossSourceResponse(BaseModel):
    signals: list[CrossSourceItem]


class PredictiveSignalItem(BaseModel):
    id: str
    symbol: str
    signal_type: str
    direction: str
    strength: float
    correlation: float | None = None
    lag_hours: int | None = None
    description: str
    generated_at: datetime


class PredictiveResponse(BaseModel):
    signals: list[PredictiveSignalItem]
