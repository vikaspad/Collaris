"""Pydantic schemas for agent request/response payloads."""
from typing import Optional
from pydantic import BaseModel


class StressRequest(BaseModel):
    scenario: str                           # "covid_2020" | "rate_spike_2022" | etc.
    custom_shocks: Optional[dict] = None    # for scenario="custom"


class MemoRequest(BaseModel):
    type: str = "call"                      # "call" | "advisory"


class CollateralOptimizeResponse(BaseModel):
    shortfall_millions: float
    recommendations: list[dict]
    summary: dict


class StressResult(BaseModel):
    scenario_id: str
    scenario_label: str
    base_nav: float
    stressed_nav: float
    nav_change_millions: float
    nav_change_pct: float
    base_utilization: float
    stressed_utilization: float
    position_impacts: list[dict]


class DashboardSummary(BaseModel):
    total_clients: int
    breach_count: int
    warning_count: int
    normal_count: int
    total_shortfall_millions: float
    highest_mrs_client: Optional[str] = None
    highest_mrs_score: Optional[float] = None
