"""
Market data ingestion — fetches live prices via yfinance and updates
portfolio market values. Falls back to stored values if fetch fails.
"""
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _make_session():
    import requests
    s = requests.Session()
    s.headers.update(_BROWSER_HEADERS)
    return s


def fetch_prices(tickers: list[str]) -> dict[str, float]:
    """
    Returns {ticker: latest_price} for each requested ticker.
    Uses per-ticker Ticker.history() with a browser User-Agent session —
    yf.download() returns empty JSON when Yahoo blocks the default Python UA.
    Falls back to empty dict (stored DB values are used).
    """
    if not tickers:
        return {}

    prices: dict[str, float] = {}
    try:
        import yfinance as yf
        session = _make_session()

        for ticker in tickers:
            try:
                t = yf.Ticker(ticker, session=session)
                hist = t.history(period="1d", interval="5m")
                if not hist.empty and "Close" in hist.columns:
                    series = hist["Close"].dropna()
                    if not series.empty:
                        prices[ticker] = float(series.iloc[-1])
            except Exception as e:
                logger.debug(f"Price fetch skipped for {ticker}: {e}")

    except Exception as e:
        logger.warning(f"Market data unavailable, using stored values: {e}")

    return prices


def refresh_portfolio_values(
    positions: list[dict],
    prices: dict[str, float]
) -> list[dict]:
    """
    Re-price positions using fetched prices.
    Only updates tickers that successfully resolved.
    Preserves sign convention (negative = short).
    """
    refreshed = []
    for pos in positions:
        ticker = pos["ticker"]
        if ticker in prices:
            # Recompute market value: abs(quantity) × price × direction sign
            sign = -1 if pos.get("direction") == "short" else 1
            new_mv = sign * abs(pos["quantity"]) * prices[ticker] / 1_000_000  # $M
            refreshed.append({**pos, "market_value": round(new_mv, 2)})
        else:
            refreshed.append(pos)
    return refreshed


def get_market_snapshot(tickers: list[str]) -> dict:
    """Returns prices dict plus a timestamp."""
    prices = fetch_prices(tickers)
    return {
        "prices": prices,
        "fetched_at": datetime.utcnow().isoformat(),
        "tickers_requested": len(tickers),
        "tickers_resolved": len(prices)
    }
