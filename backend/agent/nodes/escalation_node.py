"""
Escalation node — logs a high-severity escalation action for breach-tier clients.
Creates an AgentAction with action_type="escalate".
"""
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models import AgentAction
from backend.agent.state import AgentState


def escalation_node(state: AgentState, db: Session) -> AgentState:
    client_id = state["client_id"]
    risk = state.get("risk_score", {})

    db.add(AgentAction(
        client_id=client_id,
        action_type="escalate",
        triggered_at=datetime.utcnow(),
        memo_text=state.get("memo_draft", ""),
        recommendations={"items": state.get("recommendations", [])},
        status="pending"
    ))
    db.commit()

    return {
        **state,
        "agent_log": state.get("agent_log", []) + [
            f"[escalation] BREACH escalation logged for {client_id} — MRS={risk.get('mrs_score')}"
        ]
    }
