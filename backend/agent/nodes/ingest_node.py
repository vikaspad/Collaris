"""
Ingest node — fetches portfolio, positions, and collateral from DB
then optionally refreshes prices via yfinance.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.models import Client, Portfolio, CollateralItem, RiskScore
from backend.core.data_ingestion import get_market_snapshot
from backend.agent.state import AgentState


def ingest_node(state: AgentState, db: Session) -> AgentState:
    client_id = state["client_id"]

    # Load latest portfolio and positions
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.client_id == client_id)
        .order_by(desc(Portfolio.snapshot_time))
        .first()
    )

    positions = []
    if portfolio:
        positions = [
            {
                "ticker": p.ticker,
                "asset_class": p.asset_class,
                "quantity": p.quantity,
                "market_value": p.market_value,
                "direction": p.direction
            }
            for p in portfolio.positions
        ]

    # Load collateral items
    collateral = db.query(CollateralItem).filter(CollateralItem.client_id == client_id).all()
    collateral_dicts = [
        {
            "ticker": c.ticker,
            "asset_type": c.asset_type,
            "market_value": c.market_value,
            "haircut_pct": c.haircut_pct,
            "is_pledged": c.is_pledged,
            "eligible": c.eligible
        }
        for c in collateral
    ]

    # Fetch live prices for equity tickers (best-effort — never crashes the graph)
    equity_tickers = [p["ticker"] for p in positions if p["asset_class"] in ("equity", "etf")]
    try:
        market_data = get_market_snapshot(equity_tickers[:10])
    except Exception:
        market_data = {"prices": {}, "fetched_at": None, "tickers_requested": 0, "tickers_resolved": 0}

    # Build portfolio dict
    portfolio_dict = {}
    if portfolio:
        portfolio_dict = {
            "nav": portfolio.nav,
            "gross_exposure": portfolio.gross_exposure,
            "net_exposure": portfolio.net_exposure,
            "margin_used": portfolio.margin_used,
            "margin_available": portfolio.margin_available,
            "utilization_pct": portfolio.utilization_pct,
            "positions": positions
        }

    return {
        **state,
        "portfolio": portfolio_dict,
        "collateral_items": collateral_dicts,
        "market_data": market_data,
        "agent_log": state.get("agent_log", []) + [
            f"[ingest] Loaded {len(positions)} positions, {len(collateral_dicts)} collateral items"
        ]
    }
