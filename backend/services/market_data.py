import yfinance as yf


def get_snapshot(tickers: list[str]) -> dict[str, dict]:
    """Batch real-time price snapshot — single yfinance call for all tickers."""
    if not tickers:
        return {}
    bundle = yf.Tickers(" ".join(tickers))
    result = {}
    for ticker in tickers:
        try:
            fi = bundle.tickers[ticker].fast_info
            price = fi.last_price
            prev_close = fi.previous_close
            if price is None or prev_close is None:
                continue
            day_change = price - prev_close
            day_change_pct = (day_change / prev_close) * 100
            result[ticker] = {
                "price": price,
                "day_change_pct": day_change_pct,
                "day_change": day_change,
            }
        except Exception:
            pass
    return result


def get_all_time_high(ticker: str) -> float:
    """Max adjusted close across full available history."""
    hist = yf.Ticker(ticker).history(period="max")
    if hist.empty:
        return 0.0
    return float(hist["Close"].max())


def get_recent_news(ticker: str, limit: int = 5) -> list[dict]:
    news = yf.Ticker(ticker).news or []
    result = []
    for n in news[:limit]:
        # yfinance restructured news format in 0.2.48+; handle both shapes
        if "content" in n:
            title = n["content"].get("title", "")
            published = n["content"].get("pubDate", "")
        else:
            title = n.get("title", "")
            published = str(n.get("providerPublishTime", ""))
        result.append({"title": title, "published": published})
    return result


def get_price_history(ticker: str, days: int = 90) -> list[dict]:
    hist = yf.Ticker(ticker).history(period=f"{days}d")
    return [
        {"date": str(idx.date()), "close": float(row["Close"]), "volume": int(row["Volume"])}
        for idx, row in hist.iterrows()
    ]
