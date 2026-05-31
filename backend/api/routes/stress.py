"""
Stress test route.
POST /api/clients/{id}/stress
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.database import get_db
from backend.db.models import Client, Portfolio
from backend.api.schemas.agent import StressRequest, StressResult
from backend.core.stress_engine import run_stress_scenario, run_all_scenarios

router = APIRouter(prefix="/api/clients", tags=["stress"])


def _get_portfolio_data(client_id: str, db: Session):
    """Returns (nav, margin_used, margin_available, positions_list) or raises 404."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.client_id == client_id)
        .order_by(desc(Portfolio.snapshot_time))
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="No portfolio found")

    positions = [
        {
            "ticker": p.ticker,
            "asset_class": p.asset_class,
            "market_value": p.market_value,
            "direction": p.direction
        }
        for p in portfolio.positions
    ]
    return portfolio.nav, portfolio.margin_used, portfolio.margin_available, positions


@router.post("/{client_id}/stress", response_model=StressResult)
def run_stress(client_id: str, req: StressRequest, db: Session = Depends(get_db)):
    nav, mu, ma, positions = _get_portfolio_data(client_id, db)
    result = run_stress_scenario(req.scenario, nav, mu, ma, positions, req.custom_shocks)
    return StressResult(**result)


@router.get("/{client_id}/stress/all")
def run_all_stress(client_id: str, db: Session = Depends(get_db)):
    """Run all 4 standard scenarios at once."""
    nav, mu, ma, positions = _get_portfolio_data(client_id, db)
    return run_all_scenarios(nav, mu, ma, positions)
