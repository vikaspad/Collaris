"""
Risk Engine — MRS scoring, VaR, margin utilization, shortfall, lead time.
Every formula is defined in CLAUDE.md §8. Thresholds always come from env vars.
"""
import os
import math
from datetime import datetime
from typing import Optional

BREACH_THRESHOLD = float(os.getenv("BREACH_THRESHOLD", "85"))
WARNING_THRESHOLD = float(os.getenv("WARNING_THRESHOLD", "65"))


# ── Core formulas (tested in tests/test_risk_engine.py) ─────────────────────

def compute_utilization(margin_used: float, margin_available: float) -> float:
    """Margin used as a percentage of total margin capacity."""
    total = margin_used + margin_available
    if total <= 0:
        return 0.0
    return round((margin_used / total) * 100, 1)


def compute_shortfall(
    utilization: float,
    collateral_market_value: float,
    threshold: Optional[float] = None
) -> float:
    """
    Dollar shortfall above the breach threshold.
    Returns 0 when utilization is within limits.
    """
    threshold = threshold or BREACH_THRESHOLD
    if utilization <= threshold:
        return 0.0
    excess_pct = (utilization - threshold) / 100
    return round(excess_pct * collateral_market_value, 2)


def compute_var_1d(nav: float, gross_exposure: float, asset_class_mix: dict) -> float:
    """
    Parametric 1-day 99% VaR using assumed volatilities per asset class.
    Simplified model — replace with QuantLib in production.
    """
    # Annualised daily vol assumptions by asset class (σ)
    vol_map = {
        "equity": 0.018,
        "bond": 0.006,
        "etf": 0.014,
        "fx": 0.007,
        "commodity": 0.020,
    }
    z_99 = 2.326  # z-score for 99% confidence

    weighted_vol = sum(
        weight * vol_map.get(asset_class, 0.015)
        for asset_class, weight in asset_class_mix.items()
    )
    # VaR = exposure × weighted_vol × z-score
    var = gross_exposure * weighted_vol * z_99
    return round(var, 2)


def compute_lead_time_hours(
    utilization: float,
    trend: str,
    var_1d: float,
    nav: float
) -> float:
    """
    Estimated hours until breach at current trend velocity.
    For display purposes only — not a contractual commitment (CLAUDE.md §16.6).
    """
    if utilization >= BREACH_THRESHOLD:
        return 0.0

    headroom = BREACH_THRESHOLD - utilization  # percentage points of headroom

    # Daily drift rate based on trend
    drift_rates = {"up": 3.0, "stable": 0.5, "down": -1.0}
    daily_drift = drift_rates.get(trend, 0.5)

    # VaR contributes to how fast margin can erode
    var_component = (var_1d / max(nav, 1)) * 100 * 0.5  # pct pts per day

    total_daily = daily_drift + var_component
    if total_daily <= 0:
        return 9999.0  # effectively no breach risk

    days_to_breach = headroom / total_daily
    return round(days_to_breach * 24, 1)


def compute_mrs(
    utilization: float,
    var_1d: float,
    nav: float,
    trend: str,
    call_history_30d: int,
    stress_worst: float
) -> int:
    """
    Margin Risk Score (0–100). Formula from CLAUDE.md §8.
    Higher = more dangerous.
    """
    base = utilization * 0.5
    var_component = min((var_1d / max(nav, 1)) * 100, 30) * 0.2
    trend_adj = 10 if trend == "up" else (-5 if trend == "down" else 0)
    history_adj = min(call_history_30d * 3, 15)
    stress_adj = min(abs(stress_worst) * 0.3, 15)
    raw = base + var_component + trend_adj + history_adj + stress_adj
    return min(round(raw), 100)


def derive_status(mrs_score: int, utilization: float) -> str:
    """Translate numeric scores to a status label per CLAUDE.md §12."""
    if utilization > BREACH_THRESHOLD or mrs_score > BREACH_THRESHOLD:
        return "breach"
    if utilization >= WARNING_THRESHOLD or mrs_score >= WARNING_THRESHOLD:
        return "warning"
    return "normal"


def build_asset_class_mix(positions: list) -> dict:
    """
    Compute exposure-weighted asset class mix from a list of position dicts.
    Each dict needs keys: asset_class, market_value.
    """
    totals: dict[str, float] = {}
    gross = 0.0
    for pos in positions:
        cls = pos.get("asset_class", "equity")
        val = abs(pos.get("market_value", 0))
        totals[cls] = totals.get(cls, 0) + val
        gross += val

    if gross == 0:
        return {"equity": 1.0}
    return {cls: v / gross for cls, v in totals.items()}


def compute_full_risk(
    client_id: str,
    nav: float,
    gross_exposure: float,
    margin_used: float,
    margin_available: float,
    trend: str,
    call_history_30d: int,
    stress_worst: float,
    positions: list,
    total_collateral_mv: float
) -> dict:
    """
    One-stop risk computation that returns everything needed for a RiskScore row.
    Called by risk_node and the /risk endpoint.
    """
    utilization = compute_utilization(margin_used, margin_available)
    asset_mix = build_asset_class_mix(positions)
    var_1d = compute_var_1d(nav, gross_exposure, asset_mix)
    mrs = compute_mrs(utilization, var_1d, nav, trend, call_history_30d, stress_worst)
    shortfall = compute_shortfall(utilization, total_collateral_mv)
    lead_time = compute_lead_time_hours(utilization, trend, var_1d, nav)
    status = derive_status(mrs, utilization)

    return {
        "client_id": client_id,
        "computed_at": datetime.utcnow().isoformat(),
        "mrs_score": mrs,
        "utilization_pct": utilization,
        "shortfall_millions": shortfall,
        "lead_time_hours": lead_time,
        "trend": trend,
        "var_1d": var_1d,
        "stress_worst": stress_worst,
        "status": status
    }
