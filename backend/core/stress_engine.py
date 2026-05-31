"""
Stress Engine — applies historical and custom shock scenarios to a portfolio
and projects the resulting margin utilization.
Scenarios defined in data/stress_scenarios.json (CLAUDE.md §10).
"""
import json
import os
from pathlib import Path
from typing import Optional

SCENARIOS_FILE = Path(__file__).resolve().parents[2] / "data" / "stress_scenarios.json"


def load_scenarios() -> list[dict]:
    with open(SCENARIOS_FILE) as f:
        return json.load(f)["scenarios"]


def apply_shock(
    market_value: float,
    asset_class: str,
    equity_shock: float,
    bond_shock: float,
    fx_shock: float,
    vol_multiplier: float
) -> float:
    """
    Apply the relevant shock multiplier to a single position's market value.
    Returns the stressed market value (positive or negative).
    """
    shock_map = {
        "equity": equity_shock,
        "etf": equity_shock * 0.85,   # ETFs absorb some diversification benefit
        "bond": bond_shock,
        "fx": fx_shock,
        "commodity": equity_shock * 0.7,
    }
    shock = shock_map.get(asset_class, equity_shock)
    return market_value * (1 + shock)


def run_stress_scenario(
    scenario_id: str,
    nav: float,
    margin_used: float,
    margin_available: float,
    positions: list[dict],
    custom_shocks: Optional[dict] = None
) -> dict:
    """
    Run a single named scenario or a custom shock set.
    Returns stressed utilization, NAV change, and per-position impact.

    positions: list of dicts with keys ticker, asset_class, market_value, direction
    """
    if scenario_id == "custom" and custom_shocks:
        scenario = {
            "id": "custom",
            "label": "Custom Scenario",
            **custom_shocks
        }
    else:
        scenarios = load_scenarios()
        matches = [s for s in scenarios if s["id"] == scenario_id]
        if not matches:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        scenario = matches[0]

    eq_shock = scenario.get("equity_shock", 0.0)
    bond_shock = scenario.get("bond_shock", 0.0)
    fx_shock = scenario.get("fx_shock", 0.0)
    vol_mult = scenario.get("vol_multiplier", 1.0)

    # Apply shocks to each position
    position_impacts = []
    total_stressed_mv = 0.0
    total_base_mv = 0.0

    for pos in positions:
        base_mv = pos["market_value"]
        stressed_mv = apply_shock(
            base_mv, pos["asset_class"],
            eq_shock, bond_shock, fx_shock, vol_mult
        )
        impact = stressed_mv - base_mv
        position_impacts.append({
            "ticker": pos["ticker"],
            "base_mv": round(base_mv, 2),
            "stressed_mv": round(stressed_mv, 2),
            "impact_millions": round(impact, 2)
        })
        total_stressed_mv += abs(stressed_mv)
        total_base_mv += abs(base_mv)

    # Stressed NAV = NAV adjusted for net P&L change
    # Long positions lose value on negative shocks; shorts gain
    net_pnl = sum(
        (apply_shock(p["market_value"], p["asset_class"], eq_shock, bond_shock, fx_shock, vol_mult)
         - p["market_value"])
        for p in positions
    )
    stressed_nav = nav + net_pnl

    # Stressed margin: assume margin requirements scale up with vol_multiplier
    stressed_margin_used = margin_used * vol_mult
    stressed_margin_available = max(stressed_nav * 0.1, 0)   # rough floor

    total = stressed_margin_used + stressed_margin_available
    stressed_utilization = round((stressed_margin_used / max(total, 1)) * 100, 1)

    return {
        "scenario_id": scenario["id"],
        "scenario_label": scenario["label"],
        "base_nav": round(nav, 2),
        "stressed_nav": round(stressed_nav, 2),
        "nav_change_millions": round(net_pnl, 2),
        "nav_change_pct": round((net_pnl / max(nav, 1)) * 100, 1),
        "base_utilization": round((margin_used / max(margin_used + margin_available, 1)) * 100, 1),
        "stressed_utilization": stressed_utilization,
        "position_impacts": position_impacts
    }


def run_all_scenarios(
    nav: float,
    margin_used: float,
    margin_available: float,
    positions: list[dict]
) -> list[dict]:
    """Run all standard scenarios and return results."""
    scenarios = load_scenarios()
    results = []
    for s in scenarios:
        try:
            result = run_stress_scenario(
                s["id"], nav, margin_used, margin_available, positions
            )
            results.append(result)
        except Exception:
            pass
    return results
