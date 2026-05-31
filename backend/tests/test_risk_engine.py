"""
Unit tests for the risk engine.
Every risk calculation must have a test here (CLAUDE.md §15).
Run with: pytest backend/tests/test_risk_engine.py -v
"""
import pytest
from backend.core.risk_engine import (
    compute_utilization,
    compute_shortfall,
    compute_mrs,
    derive_status,
    build_asset_class_mix,
    compute_var_1d,
    compute_lead_time_hours
)


# ── compute_utilization ─────────────────────────────────────────────────────

def test_utilization_normal():
    assert compute_utilization(50, 50) == 50.0

def test_utilization_full():
    assert compute_utilization(100, 0) == 100.0

def test_utilization_zero():
    assert compute_utilization(0, 100) == 0.0

def test_utilization_zero_total():
    # Avoid division by zero
    assert compute_utilization(0, 0) == 0.0

def test_utilization_rounding():
    # 342 / (342 + 38) = 342/380 ≈ 90.0
    assert compute_utilization(342, 38) == 90.0


# ── compute_shortfall ───────────────────────────────────────────────────────

def test_shortfall_no_breach():
    assert compute_shortfall(80.0, 1000.0, threshold=85.0) == 0.0

def test_shortfall_at_threshold():
    assert compute_shortfall(85.0, 1000.0, threshold=85.0) == 0.0

def test_shortfall_breach():
    # (90 - 85) / 100 * 1000 = 50.0
    shortfall = compute_shortfall(90.0, 1000.0, threshold=85.0)
    assert shortfall == 50.0

def test_shortfall_small():
    # (86 - 85) / 100 * 200 = 2.0
    assert compute_shortfall(86.0, 200.0, threshold=85.0) == 2.0


# ── compute_mrs ─────────────────────────────────────────────────────────────

def test_mrs_capped_at_100():
    mrs = compute_mrs(
        utilization=100.0, var_1d=100.0, nav=100.0,
        trend="up", call_history_30d=10, stress_worst=-500.0
    )
    assert mrs == 100

def test_mrs_minimum_is_zero():
    mrs = compute_mrs(
        utilization=0.0, var_1d=0.0, nav=1000.0,
        trend="down", call_history_30d=0, stress_worst=0.0
    )
    assert mrs >= 0

def test_mrs_breach_scenario():
    # Utilization 90%, upward trend, 2 calls → should be high
    mrs = compute_mrs(
        utilization=90.0, var_1d=38.0, nav=2180.0,
        trend="up", call_history_30d=2, stress_worst=-312.0
    )
    assert mrs >= 80

def test_mrs_normal_scenario():
    # Utilization 40%, stable, no calls → should be low
    mrs = compute_mrs(
        utilization=40.0, var_1d=8.0, nav=600.0,
        trend="stable", call_history_30d=0, stress_worst=-50.0
    )
    assert mrs < 65

def test_mrs_trend_adjustment():
    base = compute_mrs(40.0, 10.0, 500.0, "stable", 0, -50.0)
    up = compute_mrs(40.0, 10.0, 500.0, "up", 0, -50.0)
    down = compute_mrs(40.0, 10.0, 500.0, "down", 0, -50.0)
    assert up > base > down


# ── derive_status ───────────────────────────────────────────────────────────

def test_status_breach_by_mrs():
    assert derive_status(90, 50.0) == "breach"

def test_status_breach_by_utilization():
    assert derive_status(60, 90.0) == "breach"

def test_status_warning():
    assert derive_status(70, 70.0) == "warning"

def test_status_normal():
    assert derive_status(30, 40.0) == "normal"

def test_status_boundary_breach():
    # Exactly at breach threshold → still breach
    assert derive_status(86, 85.1) == "breach"


# ── build_asset_class_mix ───────────────────────────────────────────────────

def test_asset_mix_sums_to_one():
    positions = [
        {"asset_class": "equity", "market_value": 100},
        {"asset_class": "bond", "market_value": 100},
    ]
    mix = build_asset_class_mix(positions)
    assert abs(sum(mix.values()) - 1.0) < 1e-6

def test_asset_mix_empty():
    # Should not crash; returns a default
    mix = build_asset_class_mix([])
    assert mix == {"equity": 1.0}

def test_asset_mix_single_class():
    positions = [{"asset_class": "equity", "market_value": 500}]
    mix = build_asset_class_mix(positions)
    assert mix["equity"] == pytest.approx(1.0)


# ── compute_var_1d ──────────────────────────────────────────────────────────

def test_var_positive():
    var = compute_var_1d(nav=1000.0, gross_exposure=2000.0, asset_class_mix={"equity": 1.0})
    assert var > 0

def test_var_scales_with_exposure():
    low = compute_var_1d(1000.0, 1000.0, {"equity": 1.0})
    high = compute_var_1d(1000.0, 2000.0, {"equity": 1.0})
    assert high > low


# ── compute_lead_time_hours ─────────────────────────────────────────────────

def test_lead_time_breach_is_zero():
    hours = compute_lead_time_hours(utilization=90.0, trend="up", var_1d=30.0, nav=1000.0)
    assert hours == 0.0

def test_lead_time_normal_positive():
    hours = compute_lead_time_hours(utilization=40.0, trend="stable", var_1d=5.0, nav=1000.0)
    assert hours > 0

def test_lead_time_downtrend_longer():
    up = compute_lead_time_hours(60.0, "up", 10.0, 1000.0)
    down = compute_lead_time_hours(60.0, "down", 10.0, 1000.0)
    assert down > up
