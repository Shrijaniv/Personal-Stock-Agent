from datetime import date, timedelta
import httpx
from config import POLYGON_API_KEY

BASE = "https://api.polygon.io"


def _get(path: str, params: dict = None) -> dict:
    params = params or {}
    params["apiKey"] = POLYGON_API_KEY
    resp = httpx.get(f"{BASE}{path}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_snapshot(tickers: list[str]) -> dict[str, dict]:
    """Batch price snapshot — 1 API call for all tickers."""
    if not tickers:
        return {}
    data = _get(
        "/v2/snapshot/locale/us/markets/stocks/tickers",
        {"tickers": ",".join(tickers)},
    )
    result = {}
    for t in data.get("tickers", []):
        ticker = t["ticker"]
        last_trade = t.get("lastTrade", {})
        day = t.get("day", {})
        result[ticker] = {
            "price": last_trade.get("p") or day.get("c") or t.get("prevDay", {}).get("c"),
            "day_change_pct": t.get("todaysChangePerc", 0.0),
            "day_change": t.get("todaysChange", 0.0),
        }
    return result


def get_all_time_high(ticker: str) -> float:
    """Fetch max daily close across all available history."""
    today = date.today().isoformat()
    data = _get(
        f"/v2/aggs/ticker/{ticker}/range/1/day/2000-01-01/{today}",
        {"adjusted": "true", "sort": "asc", "limit": 50000},
    )
    closes = [bar["c"] for bar in data.get("results", [])]
    return max(closes) if closes else 0.0


def get_recent_news(ticker: str, limit: int = 5) -> list[dict]:
    data = _get("/v2/reference/news", {"ticker": ticker, "limit": limit})
    return [
        {"title": n.get("title", ""), "published": n.get("published_utc", "")}
        for n in data.get("results", [])
    ]


def get_price_history(ticker: str, days: int = 90) -> list[dict]:
    end = date.today()
    start = end - timedelta(days=days)
    data = _get(
        f"/v2/aggs/ticker/{ticker}/range/1/day/{start.isoformat()}/{end.isoformat()}",
        {"adjusted": "true", "sort": "asc", "limit": days + 10},
    )
    return [
        {"date": bar.get("t"), "close": bar["c"], "volume": bar.get("v", 0)}
        for bar in data.get("results", [])
    ]
