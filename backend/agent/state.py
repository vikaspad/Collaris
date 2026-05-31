"""
AgentState — the single shared state dictionary passed between all LangGraph nodes.
Schema defined in CLAUDE.md §6.
"""
from typing import TypedDict, Optional


class AgentState(TypedDict):
    client_id: str
    portfolio: dict                   # Latest portfolio snapshot
    risk_score: dict                  # Computed risk metrics
    collateral_items: list[dict]      # All collateral items
    market_data: dict                 # Prices + metadata from data_ingestion
    stress_results: list[dict]        # All 4 scenario outputs
    action_tier: str                  # monitor | alert | optimize | memo | escalate
    recommendations: list[str]        # Collateral substitution suggestions
    memo_draft: str                   # LLM-generated memo text
    agent_log: list[str]              # Human-readable trace of decisions
    iteration: int                    # Safeguard against runaway loops
