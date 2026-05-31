"""
Margin Call node — creates MarginCall records and logs comms events for breach clients.
Fires only when action_tier == "breach".
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.db.models import MarginCall, AgentAction
from backend.agent.state import AgentState


def margin_call_node(state: AgentState, db: Session) -> AgentState:
    """
    For breach clients: ensures an active MarginCall row exists, then logs
    a comms AgentAction so the Margin Call tab has a communications trail.
    Skips silently for non-breach tiers.
    """
    if state.get("action_tier") != "breach":
        return state

    client_id = state["client_id"]
    risk = state.get("risk_score", {})
    shortfall = risk.get("shortfall_millions", 0.0)
    due_by = datetime.utcnow() + timedelta(hours=2)

    # Avoid duplicate calls within a 4-hour window
    recent = (
        db.query(MarginCall)
        .filter(
            MarginCall.client_id == client_id,
            MarginCall.resolved_at.is_(None),
            MarginCall.issued_at >= datetime.utcnow() - timedelta(hours=4)
        )
        .first()
    )

    if not recent:
        call = MarginCall(
            client_id=client_id,
            issued_at=datetime.utcnow(),
            shortfall_millions=shortfall,
            due_by=due_by,
        )
        db.add(call)

        # Auto-notification comms entry
        db.add(AgentAction(
            client_id=client_id,
            action_type="alert",
            triggered_at=datetime.utcnow() + timedelta(seconds=2),
            memo_text=f"House Call issued — shortfall ${shortfall:.1f}M. Due by {due_by.strftime('%H:%M')} UTC.",
            status="sent",
        ))
        db.commit()
        log_msg = f"[margin_call] New house call issued — ${shortfall:.1f}M shortfall, due {due_by.strftime('%H:%M')}"
    else:
        log_msg = f"[margin_call] Active call exists (issued {recent.issued_at.strftime('%H:%M')} UTC)"

    return {
        **state,
        "agent_log": state.get("agent_log", []) + [log_msg],
    }
