"""Pydantic response models (camelCase to match the frontend)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    status: Literal["ok"]
    dataStart: datetime
    dataEnd: datetime
    actualRows: int
    forecastRows: int


class SeriesPoint(BaseModel):
    startTime: datetime
    actual: float | None
    forecast: float | None
    error: float | None  # forecast - actual
    publishTime: datetime | None
    horizonHours: float | None


class Selection(BaseModel):
    start: datetime
    end: datetime
    mode: Literal["horizon", "decision"]
    horizon: int | None
    cutoff: str | None


class Metrics(BaseModel):
    selection: Selection
    targets: int
    withForecast: int
    paired: int
    coveragePct: float | None
    meanActual: float | None
    mae: float | None
    rmse: float | None
    bias: float | None
    nmaePct: float | None
    p10: float | None
    p50: float | None
    p90: float | None


class HorizonRow(BaseModel):
    horizon: int
    mae: float | None
    rmse: float | None
    bias: float | None
    p10: float | None
    p90: float | None
    coveragePct: float | None
    paired: int


class HourRow(BaseModel):
    hour: int
    mae: float | None
    bias: float | None
    n: int
