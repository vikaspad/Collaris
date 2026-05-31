"""
LangGraph workflow definition for the Collaris agent.

Flow:
  START → ingest → risk → route_by_severity
    breach  → margin_call → collateral → memo → escalation → END
    warning → collateral → log → END   (collateral optimised, no LLM call)
    normal  → log → END

Memo generation only fires for breach (MRS ≥ 85) — CLAUDE.md §16 rule #2.
"""
import asyncio
from typing import AsyncGenerator
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, END

from backend.agent.state import AgentState
from backend.agent.nodes.ingest_node import ingest_node
from backend.agent.nodes.risk_node import risk_node
from backend.agent.nodes.margin_call_node import margin_call_node
from backend.agent.nodes.collateral_node import collateral_node
from backend.agent.nodes.memo_node import memo_node
from backend.agent.nodes.escalation_node import escalation_node
from backend.agent.nodes.log_node import log_node


def route_by_severity(state: AgentState) -> str:
    """Conditional edge — routes based on MRS score (CLAUDE.md §6)."""
    mrs = state.get("risk_score", {}).get("mrs_score", 0)
    if mrs >= 85:
        return "breach"
    elif mrs >= 65:
        return "warning"
    return "normal"


def route_after_collateral(state: AgentState) -> str:
    """Only breach clients proceed to memo generation (CLAUDE.md §16 rule #2)."""
    return "memo" if state.get("action_tier") == "breach" else "log"


def _build_graph(db: Session):
    """Builds the compiled LangGraph workflow with DB session injected."""

    # Wrap sync nodes to accept state only (db injected via closure)
    def _ingest(state): return ingest_node(state, db)
    def _risk(state): return risk_node(state, db)
    def _margin_call(state): return margin_call_node(state, db)
    def _collateral(state): return collateral_node(state, db)
    def _escalation(state): return escalation_node(state, db)
    def _log(state): return log_node(state, db)

    # Memo node is async — wrap it
    async def _memo(state): return await memo_node(state, db)

    graph = StateGraph(AgentState)

    graph.add_node("ingest", _ingest)
    graph.add_node("risk", _risk)
    graph.add_node("margin_call", _margin_call)
    graph.add_node("collateral", _collateral)
    graph.add_node("memo", _memo)
    graph.add_node("escalation", _escalation)
    graph.add_node("log", _log)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "risk")

    # breach → margin_call (create/update MC record) → collateral → memo → escalation
    # warning → collateral → memo → escalation
    graph.add_conditional_edges(
        "risk",
        route_by_severity,
        {
            "breach": "margin_call",
            "warning": "collateral",
            "normal": "log"
        }
    )

    graph.add_edge("margin_call", "collateral")

    # breach → memo → escalation; warning/normal → log
    graph.add_conditional_edges(
        "collateral",
        route_after_collateral,
        {"memo": "memo", "log": "log"}
    )

    graph.add_edge("memo", "escalation")
    graph.add_edge("escalation", END)
    graph.add_edge("log", END)

    return graph.compile()


async def run_agent_for_client(client_id: str, db: Session) -> AgentState:
    """Run the full agent graph and return final state."""
    initial_state: AgentState = {
        "client_id": client_id,
        "portfolio": {},
        "risk_score": {},
        "collateral_items": [],
        "market_data": {},
        "stress_results": [],
        "action_tier": "monitor",
        "recommendations": [],
        "memo_draft": "",
        "agent_log": [],
        "iteration": 0
    }

    compiled = _build_graph(db)
    final_state = await compiled.ainvoke(initial_state)
    return final_state


async def stream_agent_for_client(
    client_id: str, db: Session
) -> AsyncGenerator[dict, None]:
    """
    Stream individual node outputs as they complete.
    Used by the SSE endpoint to push reasoning steps to the frontend.
    """
    initial_state: AgentState = {
        "client_id": client_id,
        "portfolio": {},
        "risk_score": {},
        "collateral_items": [],
        "market_data": {},
        "stress_results": [],
        "action_tier": "monitor",
        "recommendations": [],
        "memo_draft": "",
        "agent_log": [],
        "iteration": 0
    }

    compiled = _build_graph(db)

    async for chunk in compiled.astream(initial_state):
        for node_name, node_state in chunk.items():
            log = node_state.get("agent_log", [])
            latest_log = log[-1] if log else ""
            yield {
                "node": node_name,
                "log": latest_log,
                "action_tier": node_state.get("action_tier", ""),
                "mrs_score": node_state.get("risk_score", {}).get("mrs_score"),
            }
            await asyncio.sleep(0)
