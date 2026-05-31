"""
Margin Call routes.
GET  /api/clients/{id}/margin-call/active  — active call with full detail
POST /api/clients/{id}/margin-call/{call_id}/acknowledge
POST /api/clients/{id}/margin-call/{call_id}/resolve
"""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.database import get_db
from backend.db.models import Client, MarginCall, Portfolio, AgentAction
from backend.core.collateral_optimizer import optimize_collateral, CollateralAsset

router = APIRouter(prefix="/api/clients", tags=["margin-call"])

BREACH_THRESHOLD = float(os.getenv("BREACH_THRESHOLD", "85"))

# Approximate margin rates per asset class (initialMargin %)
_MARGIN_RATES = {
    "equity": 0.15,
    "bond": 0.05,
    "etf": 0.10,
    "fx": 0.08,
    "commodity": 0.18,
}


def _fmt_call_id(call_id: int) -> str:
    return f"MC-{datetime.utcnow().year}-{call_id:04d}"


def _resolved_duration(call: MarginCall) -> str:
    if not call.resolved_at:
        return "—"
    delta = call.resolved_at - call.issued_at
    total_mins = int(delta.total_seconds() / 60)
    h, m = divmod(total_mins, 60)
    return f"{h}h {m}m" if h else f"{m}m"


def _position_breakdown(portfolio: Portfolio) -> list[dict]:
    """Compute per-position margin requirements and shortfall contribution."""
    if not portfolio or not portfolio.positions:
        return []

    gross = max(abs(portfolio.gross_exposure), 1.0)
    breakdown = []
    for p in portfolio.positions:
        rate = _MARGIN_RATES.get(p.asset_class, 0.15)
        market_val = abs(p.market_value)
        margin_req = round(market_val * rate, 2)
        # Distribute available margin proportional to position size
        allocated = portfolio.margin_available * (market_val / gross)
        excess = round(allocated - margin_req, 2)
        breakdown.append({
            "ticker": p.ticker,
            "direction": p.direction,
            "market_value": round(market_val, 2),
            "margin_req": margin_req,
            "excess": excess,
        })

    # Compute contribution only for positions with a deficit
    total_deficit = sum(abs(b["excess"]) for b in breakdown if b["excess"] < 0) or 1.0
    for b in breakdown:
        b["contribution_pct"] = (
            round(abs(b["excess"]) / total_deficit * 100) if b["excess"] < 0 else 0
        )

    breakdown.sort(key=lambda x: x["contribution_pct"], reverse=True)
    return breakdown


def _resolution_options(client, shortfall: float) -> list[dict]:
    """Generate resolution pathways: cash deposit, collateral sub, position reduction."""
    assets = [
        CollateralAsset(
            ticker=c.ticker, asset_type=c.asset_type,
            market_value=c.market_value, haircut_pct=c.haircut_pct,
            is_pledged=c.is_pledged, eligible=c.eligible,
        )
        for c in client.collateral_items
    ]
    optimizer_recs = optimize_collateral(assets, shortfall)
    total_freed = sum(r["frees_millions"] for r in optimizer_recs)

    options = [
        {
            "type": "Cash Deposit",
            "amount": shortfall,
            "time_to_settle": "T+0",
            "feasibility": "High",
            "notes": "Wire transfer to PB margin account. Fastest resolution path.",
        }
    ]

    if optimizer_recs:
        parts = [f"{r['action']} — frees ${r['frees_millions']}M" for r in optimizer_recs[:2]]
        options.append({
            "type": "Collateral Substitution",
            "amount": round(total_freed, 2),
            "time_to_settle": "T+0",
            "feasibility": "High" if total_freed >= shortfall * 0.9 else "Medium",
            "notes": "; ".join(parts),
        })

    options.append({
        "type": "Position Reduction",
        "amount": shortfall,
        "time_to_settle": "T+0",
        "feasibility": "Medium",
        "notes": "Reduce largest contributing positions to lower margin requirement.",
    })

    return options


def _comms_log(client_id: str, call_issued_at: datetime, db: Session) -> list[dict]:
    """Build comms timeline from AgentAction entries near the call issuance."""
    actions = (
        db.query(AgentAction)
        .filter(
            AgentAction.client_id == client_id,
            AgentAction.triggered_at >= call_issued_at - timedelta(minutes=5),
        )
        .order_by(AgentAction.triggered_at)
        .limit(10)
        .all()
    )

    type_map = {
        "alert": "issued", "memo": "notified",
        "escalate": "escalated", "monitor": "ack",
    }
    actor_map = {
        "alert": "System", "memo": "Agent",
        "escalate": "Coverage", "monitor": "Agent",
    }

    log = []
    for a in actions:
        log.append({
            "time": a.triggered_at.strftime("%H:%M"),
            "event": (a.memo_text or a.action_type.capitalize())[:120],
            "actor": actor_map.get(a.action_type, "System"),
            "type": type_map.get(a.action_type, "notified"),
        })

    # Ensure the issuance event is always first
    issue = {
        "time": call_issued_at.strftime("%H:%M"),
        "event": "House Call issued automatically by risk engine",
        "actor": "System",
        "type": "issued",
    }
    if not log or log[0]["type"] != "issued":
        log.insert(0, issue)

    return log


def _consequences(due_by: datetime) -> list[dict]:
    t2 = due_by
    t4 = due_by + timedelta(hours=2)
    return [
        {"time": f"T+2h ({t2.strftime('%H:%M')})", "event": "Forced liquidation begins — smallest positions first", "severity": "high"},
        {"time": f"T+4h ({t4.strftime('%H:%M')})", "event": "Reg T Fed Call issued if shortfall unresolved", "severity": "high"},
        {"time": "T+EOD", "event": "Account flagged for credit review, leverage reduced 20%", "severity": "medium"},
        {"time": "T+3d", "event": "Potential suspension of new position opening", "severity": "medium"},
    ]


@router.get("/{client_id}/margin-call/active")
def get_active_margin_call(client_id: str, db: Session = Depends(get_db)):
    """Active margin call with position breakdown, resolution options, comms log, and history."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    active_call = (
        db.query(MarginCall)
        .filter(MarginCall.client_id == client_id, MarginCall.resolved_at.is_(None))
        .order_by(desc(MarginCall.issued_at))
        .first()
    )

    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.client_id == client_id)
        .order_by(desc(Portfolio.snapshot_time))
        .first()
    )

    history = (
        db.query(MarginCall)
        .filter(MarginCall.client_id == client_id, MarginCall.resolved_at.isnot(None))
        .order_by(desc(MarginCall.issued_at))
        .limit(10)
        .all()
    )
    history_list = [
        {
            "date": h.issued_at.strftime("%b %d"),
            "call_id": _fmt_call_id(h.id),
            "shortfall": h.shortfall_millions,
            "type": "House Call",
            "resolved_in": _resolved_duration(h),
            "resolution": (h.resolution_type or "Unknown").replace("_", " ").title(),
        }
        for h in history
    ]

    if not active_call:
        return {"active_call": None, "position_breakdown": [], "resolution_options": [],
                "comms_log": [], "consequences": [], "history": history_list}

    shortfall = active_call.shortfall_millions

    return {
        "active_call": {
            "id": active_call.id,
            "call_id": _fmt_call_id(active_call.id),
            "type": "House Call",
            "issued_at": active_call.issued_at.strftime("%H:%M"),
            "due_by": active_call.due_by.strftime("%H:%M") if active_call.due_by else "N/A",
            "due_by_iso": active_call.due_by.isoformat() if active_call.due_by else None,
            "shortfall_millions": shortfall,
            "regulation": "Internal PB Policy",
            "issued_by": "Risk Desk — Auto",
            "acknowledged_at": None,
            "status": "pending",
        },
        "position_breakdown": _position_breakdown(portfolio),
        "resolution_options": _resolution_options(client, shortfall),
        "comms_log": _comms_log(client_id, active_call.issued_at, db),
        "consequences": _consequences(active_call.due_by) if active_call.due_by else [],
        "history": history_list,
    }


@router.post("/{client_id}/margin-call/{call_id}/acknowledge")
def acknowledge_margin_call(client_id: str, call_id: int, db: Session = Depends(get_db)):
    call = db.query(MarginCall).filter(
        MarginCall.id == call_id, MarginCall.client_id == client_id
    ).first()
    if not call:
        raise HTTPException(status_code=404, detail="Margin call not found")

    db.add(AgentAction(
        client_id=client_id,
        action_type="monitor",
        triggered_at=datetime.utcnow(),
        memo_text=f"{_fmt_call_id(call_id)} acknowledged by client operations",
        status="acknowledged",
    ))
    db.commit()
    return {"status": "acknowledged", "call_id": call_id}


@router.post("/{client_id}/margin-call/{call_id}/resolve")
def resolve_margin_call(
    client_id: str, call_id: int,
    resolution_type: str = "deposit",
    db: Session = Depends(get_db),
):
    call = db.query(MarginCall).filter(
        MarginCall.id == call_id, MarginCall.client_id == client_id
    ).first()
    if not call:
        raise HTTPException(status_code=404, detail="Margin call not found")

    call.resolved_at = datetime.utcnow()
    call.resolution_type = resolution_type
    db.add(AgentAction(
        client_id=client_id,
        action_type="monitor",
        triggered_at=datetime.utcnow(),
        memo_text=f"{_fmt_call_id(call_id)} resolved via {resolution_type}",
        status="acknowledged",
    ))
    db.commit()
    return {"status": "resolved", "resolution_type": resolution_type}
