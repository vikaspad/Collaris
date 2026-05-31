"""
Client routes — list and detail endpoints.
GET /api/clients
GET /api/clients/{id}
GET /api/clients/{id}/portfolio
GET /api/clients/{id}/history
GET /api/clients/{id}/calls
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.database import get_db
from backend.db.models import Client, Portfolio, RiskScore, MarginCall
from backend.api.schemas.client import (
    ClientSummarySchema, ClientDetailSchema,
    PortfolioSchema, MarginCallSchema, RiskScoreSchema
)

router = APIRouter(prefix="/api/clients", tags=["clients"])


def _latest_risk(client_id: str, db: Session) -> RiskScore | None:
    return (
        db.query(RiskScore)
        .filter(RiskScore.client_id == client_id)
        .order_by(desc(RiskScore.computed_at))
        .first()
    )


def _latest_portfolio(client_id: str, db: Session) -> Portfolio | None:
    return (
        db.query(Portfolio)
        .filter(Portfolio.client_id == client_id)
        .order_by(desc(Portfolio.snapshot_time))
        .first()
    )


@router.get("", response_model=list[ClientSummarySchema])
def list_clients(db: Session = Depends(get_db)):
    """All clients with their current status and top risk metrics."""
    clients = db.query(Client).order_by(Client.id).all()
    result = []
    for c in clients:
        risk = _latest_risk(c.id, db)
        result.append(ClientSummarySchema(
            id=c.id,
            name=c.name,
            strategy=c.strategy,
            aum_millions=c.aum_millions,
            status=c.status,
            mrs_score=risk.mrs_score if risk else None,
            utilization_pct=risk.utilization_pct if risk else None,
            shortfall_millions=risk.shortfall_millions if risk else None,
            trend=risk.trend if risk else None
        ))
    return result


@router.get("/{client_id}", response_model=ClientDetailSchema)
def get_client(client_id: str, db: Session = Depends(get_db)):
    """Full client detail including latest portfolio, risk score, and collateral."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    portfolio = _latest_portfolio(client_id, db)
    risk = _latest_risk(client_id, db)

    return ClientDetailSchema(
        id=client.id,
        name=client.name,
        strategy=client.strategy,
        aum_millions=client.aum_millions,
        status=client.status,
        created_at=client.created_at,
        latest_portfolio=PortfolioSchema.model_validate(portfolio) if portfolio else None,
        latest_risk=RiskScoreSchema.model_validate(risk) if risk else None,
        collateral=[c for c in client.collateral_items]
    )


@router.get("/{client_id}/portfolio", response_model=PortfolioSchema)
def get_portfolio(client_id: str, db: Session = Depends(get_db)):
    portfolio = _latest_portfolio(client_id, db)
    if not portfolio:
        raise HTTPException(status_code=404, detail="No portfolio found")
    return portfolio


@router.get("/{client_id}/risk", response_model=RiskScoreSchema)
def get_risk(client_id: str, db: Session = Depends(get_db)):
    risk = _latest_risk(client_id, db)
    if not risk:
        raise HTTPException(status_code=404, detail="No risk score found")
    return risk


@router.get("/{client_id}/history")
def get_history(client_id: str, db: Session = Depends(get_db)):
    """30-day MRS and utilization history for sparklines."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    history = (
        db.query(RiskScore)
        .filter(RiskScore.client_id == client_id)
        .order_by(RiskScore.computed_at)
        .limit(30)
        .all()
    )
    return [
        {
            "date": r.computed_at.isoformat(),
            "mrs_score": r.mrs_score,
            "utilization_pct": r.utilization_pct
        }
        for r in history
    ]


@router.get("/{client_id}/calls", response_model=list[MarginCallSchema])
def get_calls(client_id: str, db: Session = Depends(get_db)):
    """Margin call history for a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    return (
        db.query(MarginCall)
        .filter(MarginCall.client_id == client_id)
        .order_by(desc(MarginCall.issued_at))
        .all()
    )
