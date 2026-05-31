"""
Log node — used for normal-tier clients to record a monitor action.
"""
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models import AgentAction
from backend.agent.state import AgentState


def log_node(state: AgentState, db: Session) -> AgentState:
    client_id = state["client_id"]
    risk = state.get("risk_score", {})

    db.add(AgentAction(
        client_id=client_id,
        action_type="monitor",
        triggered_at=datetime.utcnow(),
        status="acknowledged"
    ))
    db.commit()

    return {
        **state,
        "agent_log": state.get("agent_log", []) + [
            f"[log] Normal — monitoring {client_id}, MRS={risk.get('mrs_score')}"
        ]
    }
