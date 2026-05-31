"""
Collateral node — runs the LP optimizer and appends recommendations to state.
Only reached for warning and breach tiers.
"""
from sqlalchemy.orm import Session

from backend.core.collateral_optimizer import optimize_collateral, CollateralAsset
from backend.agent.state import AgentState


def collateral_node(state: AgentState, db: Session) -> AgentState:
    collateral = state.get("collateral_items", [])
    risk = state.get("risk_score", {})
    shortfall = risk.get("shortfall_millions", 0.0)

    assets = [
        CollateralAsset(
            ticker=c["ticker"],
            asset_type=c["asset_type"],
            market_value=c["market_value"],
            haircut_pct=c["haircut_pct"],
            is_pledged=c["is_pledged"],
            eligible=c["eligible"]
        )
        for c in collateral
    ]

    recs = optimize_collateral(assets, shortfall)
    rec_strings = [r["action"] + f" — frees ${r['frees_millions']}M (haircut {r['haircut']})" for r in recs]

    return {
        **state,
        "recommendations": rec_strings,
        "agent_log": state.get("agent_log", []) + [
            f"[collateral] {len(recs)} substitution(s) identified, total shortfall ${shortfall}M"
        ]
    }
