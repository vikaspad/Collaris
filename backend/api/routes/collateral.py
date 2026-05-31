"""
Collateral routes.
GET /api/clients/{id}/collateral
GET /api/clients/{id}/collateral/optimize
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.database import get_db
from backend.db.models import Client, CollateralItem, RiskScore
from backend.api.schemas.client import CollateralItemSchema
from backend.api.schemas.agent import CollateralOptimizeResponse
from backend.core.collateral_optimizer import (
    optimize_collateral, get_collateral_summary, CollateralAsset
)

router = APIRouter(prefix="/api/clients", tags=["collateral"])


@router.get("/{client_id}/collateral", response_model=list[CollateralItemSchema])
def get_collateral(client_id: str, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client.collateral_items


@router.get("/{client_id}/collateral/optimize", response_model=CollateralOptimizeResponse)
def optimize(client_id: str, db: Session = Depends(get_db)):
    """Run LP optimizer to resolve current shortfall."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    # Get current shortfall from latest risk score
    latest_risk = (
        db.query(RiskScore)
        .filter(RiskScore.client_id == client_id)
        .order_by(desc(RiskScore.computed_at))
        .first()
    )
    shortfall = latest_risk.shortfall_millions if latest_risk else 0.0

    # Build asset list for optimizer
    assets = [
        CollateralAsset(
            ticker=c.ticker,
            asset_type=c.asset_type,
            market_value=c.market_value,
            haircut_pct=c.haircut_pct,
            is_pledged=c.is_pledged,
            eligible=c.eligible
        )
        for c in client.collateral_items
    ]

    recommendations = optimize_collateral(assets, shortfall)
    summary = get_collateral_summary(assets)

    return CollateralOptimizeResponse(
        shortfall_millions=shortfall,
        recommendations=recommendations,
        summary=summary
    )
