"""
Collateral Optimizer — greedy LP-style selection of the most efficient
unencumbered assets to pledge in order to resolve a margin shortfall.
Algorithm from CLAUDE.md §9.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class CollateralAsset:
    """Lightweight view of a CollateralItem used by the optimizer."""
    ticker: str
    asset_type: str
    market_value: float
    haircut_pct: float
    is_pledged: bool
    eligible: bool


def optimize_collateral(
    assets: list[CollateralAsset],
    shortfall: float
) -> list[dict]:
    """
    Returns a ranked list of substitution recommendations.
    Only considers eligible, unpledged assets (CLAUDE.md §16.3).
    Greedy: highest freed_value/haircut first.
    """
    if shortfall <= 0:
        return []

    eligible = [a for a in assets if a.eligible and not a.is_pledged]
    if not eligible:
        return []

    # Pre-compute freed value (market value after haircut) and efficiency score
    scored = sorted(
        [
            {
                "asset": a,
                "freed": a.market_value * (1 - a.haircut_pct / 100),
                "haircut": a.haircut_pct,
                "efficiency": (a.market_value * (1 - a.haircut_pct / 100)) / max(a.haircut_pct, 0.01)
            }
            for a in eligible
        ],
        key=lambda x: x["efficiency"],
        reverse=True  # most efficient first
    )

    selected = []
    total_freed = 0.0

    for item in scored:
        if total_freed >= shortfall:
            break
        selected.append({
            "action": f"Pledge {item['asset'].ticker} ({item['asset'].asset_type.replace('_', ' ').title()})",
            "ticker": item["asset"].ticker,
            "asset_type": item["asset"].asset_type,
            "frees_millions": round(item["freed"], 2),
            "haircut": f"{item['haircut']}%",
            "market_value_millions": round(item["asset"].market_value, 2)
        })
        total_freed += item["freed"]

    return selected


def get_collateral_summary(assets: list[CollateralAsset]) -> dict:
    """Aggregated stats used in the Collateral tab."""
    total_mv = sum(a.market_value for a in assets)
    pledged_mv = sum(a.market_value for a in assets if a.is_pledged)
    unpledged_mv = sum(a.market_value for a in assets if not a.is_pledged and a.eligible)

    # Weighted-average haircut across all assets
    if total_mv > 0:
        wa_haircut = sum(a.market_value * a.haircut_pct for a in assets) / total_mv
    else:
        wa_haircut = 0.0

    return {
        "total_collateral_mv": round(total_mv, 2),
        "pledged_mv": round(pledged_mv, 2),
        "unpledged_eligible_mv": round(unpledged_mv, 2),
        "weighted_avg_haircut_pct": round(wa_haircut, 2)
    }
