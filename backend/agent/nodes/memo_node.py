"""
Memo node — calls the LLM to draft a formal margin call or advisory memo.
Also exposes generate_memo_text() for the direct /agent/memo API endpoint.
"""
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.models import Client, RiskScore, AgentAction
from backend.agent.prompts import MARGIN_CALL_MEMO_PROMPT, ADVISORY_MEMO_PROMPT
from backend.agent.state import AgentState

logger = logging.getLogger(__name__)


def _get_llm_client():
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def _call_llm(prompt: str) -> str:
    """Single LLM call — returns the assistant text."""
    model = os.getenv("AGENT_MODEL", "gpt-4o-mini")
    max_tokens = int(os.getenv("AGENT_MAX_TOKENS", "1000"))
    client = _get_llm_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.4
    )
    return response.choices[0].message.content.strip()


async def memo_node(state: AgentState, db: Session) -> AgentState:
    """LangGraph node: generates memo based on action_tier."""
    client_id = state["client_id"]
    risk = state.get("risk_score", {})
    recs = state.get("recommendations", [])

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return {**state, "memo_draft": "", "agent_log": state.get("agent_log", []) + ["[memo] Client not found"]}

    action_tier = state.get("action_tier", "normal")
    due_by = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M UTC")

    if action_tier == "breach":
        prompt = MARGIN_CALL_MEMO_PROMPT.format(
            client_name=client.name,
            client_id=client.id,
            shortfall=risk.get("shortfall_millions", 0),
            utilization=risk.get("utilization_pct", 0),
            due_by=due_by,
            recommendations="\n".join(recs[:2]) if recs else "No substitutions available"
        )
        action_type = "memo"
    else:
        prompt = ADVISORY_MEMO_PROMPT.format(
            client_name=client.name,
            client_id=client.id,
            strategy=client.strategy,
            mrs=risk.get("mrs_score", 0),
            utilization=risk.get("utilization_pct", 0),
            trend=risk.get("trend", "stable"),
            lead_time=risk.get("lead_time_hours", 99)
        )
        action_type = "alert"

    try:
        memo_text = await _call_llm(prompt)
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        memo_text = f"[Memo generation failed: {e}]"

    # Persist to AgentAction
    db.add(AgentAction(
        client_id=client_id,
        action_type=action_type,
        triggered_at=datetime.utcnow(),
        memo_text=memo_text,
        recommendations={"items": recs},
        status="pending"
    ))
    db.commit()

    return {
        **state,
        "memo_draft": memo_text,
        "agent_log": state.get("agent_log", []) + [f"[memo] {action_type} memo drafted ({len(memo_text)} chars)"]
    }


async def generate_memo_text(client_id: str, memo_type: str, db: Session) -> str:
    """
    Called directly from the /agent/memo endpoint (no full graph run).
    memo_type: "call" | "advisory"
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError(f"Client {client_id} not found")

    risk = (
        db.query(RiskScore)
        .filter(RiskScore.client_id == client_id)
        .order_by(desc(RiskScore.computed_at))
        .first()
    )

    from backend.core.collateral_optimizer import optimize_collateral, CollateralAsset
    assets = [
        CollateralAsset(
            ticker=c.ticker, asset_type=c.asset_type, market_value=c.market_value,
            haircut_pct=c.haircut_pct, is_pledged=c.is_pledged, eligible=c.eligible
        )
        for c in client.collateral_items
    ]
    shortfall = risk.shortfall_millions if risk else 0.0
    recs = optimize_collateral(assets, shortfall)
    rec_strings = [r["action"] + f" — frees ${r['frees_millions']}M" for r in recs[:2]]
    due_by = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M UTC")

    if memo_type == "call":
        prompt = MARGIN_CALL_MEMO_PROMPT.format(
            client_name=client.name,
            client_id=client.id,
            shortfall=risk.shortfall_millions if risk else 0,
            utilization=risk.utilization_pct if risk else 0,
            due_by=due_by,
            recommendations="\n".join(rec_strings) or "No substitutions available"
        )
    else:
        prompt = ADVISORY_MEMO_PROMPT.format(
            client_name=client.name,
            client_id=client.id,
            strategy=client.strategy,
            mrs=risk.mrs_score if risk else 0,
            utilization=risk.utilization_pct if risk else 0,
            trend=risk.trend if risk else "stable",
            lead_time=risk.lead_time_hours if risk else 99
        )

    memo_text = await _call_llm(prompt)

    db.add(AgentAction(
        client_id=client_id,
        action_type="memo" if memo_type == "call" else "alert",
        triggered_at=datetime.utcnow(),
        memo_text=memo_text,
        status="pending"
    ))
    db.commit()

    return memo_text
