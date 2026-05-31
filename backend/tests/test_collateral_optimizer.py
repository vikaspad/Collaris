"""
Unit tests for the collateral optimizer.
"""
import pytest
from backend.core.collateral_optimizer import optimize_collateral, get_collateral_summary, CollateralAsset


def _make_asset(ticker="AAPL", asset_type="single_name_equity", mv=50.0,
                haircut=12.0, pledged=False, eligible=True):
    return CollateralAsset(
        ticker=ticker, asset_type=asset_type, market_value=mv,
        haircut_pct=haircut, is_pledged=pledged, eligible=eligible
    )


def test_no_shortfall_returns_empty():
    assets = [_make_asset()]
    assert optimize_collateral(assets, 0.0) == []


def test_only_eligible_unpledged():
    # Pledged asset should be excluded
    pledged = _make_asset("PLEDGED", pledged=True)
    # Ineligible asset should be excluded
    ineligible = _make_asset("INELIG", eligible=False)
    available = _make_asset("AVAIL", mv=100.0, haircut=5.0)

    result = optimize_collateral([pledged, ineligible, available], shortfall=10.0)
    assert len(result) == 1
    assert result[0]["ticker"] == "AVAIL"


def test_sufficient_assets_resolve_shortfall():
    assets = [_make_asset("T", "us_treasury", mv=100.0, haircut=2.0)]
    result = optimize_collateral(assets, shortfall=50.0)
    assert len(result) == 1
    assert result[0]["frees_millions"] == pytest.approx(98.0)


def test_multiple_assets_efficient_first():
    low_haircut = _make_asset("TREASURY", "us_treasury", mv=50.0, haircut=2.0)   # high efficiency
    high_haircut = _make_asset("HY", "high_yield_bond", mv=50.0, haircut=17.5)    # low efficiency
    result = optimize_collateral([high_haircut, low_haircut], shortfall=10.0)
    # Treasury should come first
    assert result[0]["ticker"] == "TREASURY"


def test_no_eligible_assets():
    all_pledged = [_make_asset(pledged=True)]
    assert optimize_collateral(all_pledged, shortfall=10.0) == []


def test_summary_totals():
    assets = [
        _make_asset("A", mv=100.0, pledged=True),
        _make_asset("B", mv=60.0, pledged=False),
    ]
    summary = get_collateral_summary(assets)
    assert summary["total_collateral_mv"] == pytest.approx(160.0)
    assert summary["pledged_mv"] == pytest.approx(100.0)
    assert summary["unpledged_eligible_mv"] == pytest.approx(60.0)
