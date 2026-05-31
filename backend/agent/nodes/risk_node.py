"""
Risk node — computes MRS, VaR, shortfall, lead time, and determines
the action tier used to route the rest of the graph.
"""
from sqlalchemy.orm import Session
from datetime import datetime

from backend.db.models import Client, RiskScore
from backend.core.risk_engine import compute_full_risk, derive_status
from backend.agent.state import AgentState

# Default trend and call history when not known from previous state
_DEFAULT_TREND = "stable"
_DEFAULT_CALLS = 0


def risk_node(state: AgentState, db: Session) -> AgentState:
    client_id = state["client_id"]
    portfolio = state.get("portfolio", {})
    collateral = state.get("collateral_items", [])

    if not portfolio:
        return {
            **state,
            "risk_score": {},
            "action_tier": "monitor",
            "agent_log": state.get("agent_log", []) + ["[risk] No portfolio data — defaulting to monitor"]
        }

    total_collateral_mv = sum(c["market_value"] for c in collateral)

    # Retrieve call history from DB for the MRS formula
    client = db.query(Client).filter(Client.id == client_id).first()
    from sqlalchemy import desc, func
    from backend.db.models import MarginCall
    from datetime import timedelta
    call_history_30d = (
        db.query(func.count(MarginCall.id))
        .filter(
            MarginCall.client_id == client_id,
            MarginCall.issued_at >= datetime.utcnow() - timedelta(days=30)
        )
        .scalar() or 0
    )

    # Determine trend from previous risk scores
    previous_scores = (
        db.query(RiskScore)
        .filter(RiskScore.client_id == client_id)
        .order_by(desc(RiskScore.computed_at))
        .limit(3)
        .all()
    )
    if len(previous_scores) >= 2:
        delta = previous_scores[0].utilization_pct - previous_scores[-1].utilization_pct
        trend = "up" if delta > 2 else ("down" if delta < -2 else "stable")
    else:
        trend = _DEFAULT_TREND

    # Use previous stress_worst from stored risk score if available
    stress_worst = previous_scores[0].stress_worst if previous_scores else -100.0

    risk = compute_full_risk(
        client_id=client_id,
        nav=portfolio["nav"],
        gross_exposure=portfolio["gross_exposure"],
        margin_used=portfolio["margin_used"],
        margin_available=portfolio["margin_available"],
        trend=trend,
        call_history_30d=call_history_30d,
        stress_worst=stress_worst,
        positions=portfolio.get("positions", []),
        total_collateral_mv=total_collateral_mv
    )

    # Persist new risk score to DB
    db.add(RiskScore(
        client_id=client_id,
        computed_at=datetime.utcnow(),
        mrs_score=risk["mrs_score"],
        utilization_pct=risk["utilization_pct"],
        shortfall_millions=risk["shortfall_millions"],
        lead_time_hours=risk["lead_time_hours"],
        trend=risk["trend"],
        var_1d=risk["var_1d"],
        stress_worst=risk["stress_worst"]
    ))

    # Update client status in DB
    if client:
        client.status = risk["status"]
    db.commit()

    # Determine action tier from MRS
    mrs = risk["mrs_score"]
    if mrs >= 85:
        action_tier = "breach"
    elif mrs >= 65:
        action_tier = "warning"
    else:
        action_tier = "normal"

    return {
        **state,
        "risk_score": risk,
        "action_tier": action_tier,
        "agent_log": state.get("agent_log", []) + [
            f"[risk] MRS={mrs}, util={risk['utilization_pct']}%, tier={action_tier}"
        ]
    }
