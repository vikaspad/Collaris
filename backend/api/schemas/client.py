"""Pydantic response schemas for client and portfolio data."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PositionSchema(BaseModel):
    id: int
    ticker: str
    asset_class: str
    quantity: float
    market_value: float
    direction: str

    class Config:
        from_attributes = True


class PortfolioSchema(BaseModel):
    id: int
    client_id: str
    snapshot_time: datetime
    nav: float
    gross_exposure: float
    net_exposure: float
    margin_used: float
    margin_available: float
    utilization_pct: float
    positions: list[PositionSchema] = []

    class Config:
        from_attributes = True


class CollateralItemSchema(BaseModel):
    id: int
    client_id: str
    asset_type: str
    ticker: str
    face_value: float
    market_value: float
    haircut_pct: float
    is_pledged: bool
    eligible: bool

    class Config:
        from_attributes = True


class RiskScoreSchema(BaseModel):
    id: int
    client_id: str
    computed_at: datetime
    mrs_score: float
    utilization_pct: float
    shortfall_millions: float
    lead_time_hours: float
    trend: str
    var_1d: float
    stress_worst: float

    class Config:
        from_attributes = True


class ClientSummarySchema(BaseModel):
    id: str
    name: str
    strategy: str
    aum_millions: float
    status: str
    mrs_score: Optional[float] = None
    utilization_pct: Optional[float] = None
    shortfall_millions: Optional[float] = None
    trend: Optional[str] = None

    class Config:
        from_attributes = True


class ClientDetailSchema(BaseModel):
    id: str
    name: str
    strategy: str
    aum_millions: float
    status: str
    created_at: datetime
    latest_portfolio: Optional[PortfolioSchema] = None
    latest_risk: Optional[RiskScoreSchema] = None
    collateral: list[CollateralItemSchema] = []

    class Config:
        from_attributes = True


class MarginCallSchema(BaseModel):
    id: int
    client_id: str
    issued_at: datetime
    shortfall_millions: float
    due_by: datetime
    resolved_at: Optional[datetime] = None
    resolution_type: Optional[str] = None

    class Config:
        from_attributes = True


class AgentActionSchema(BaseModel):
    id: int
    client_id: str
    action_type: str
    triggered_at: datetime
    memo_text: Optional[str] = None
    recommendations: Optional[dict] = None
    status: str

    class Config:
        from_attributes = True
