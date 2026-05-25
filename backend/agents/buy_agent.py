from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models import Watchlist, Notification
from services.market_data import get_snapshot, get_recent_news, get_price_history
from services.claude_client import analyze
from services.telegram import send_message

_DEDUP_WINDOW = timedelta(hours=4)
_DAY_DROP_THRESHOLD = -5.0


def _already_alerted(db: Session, ticker: str) -> bool:
    cutoff = datetime.now(timezone.utc) - _DEDUP_WINDOW
    return (
        db.query(Notification)
        .filter(
            Notification.ticker == ticker,
            Notification.type == "BUY",
            Notification.sent_at >= cutoff,
        )
        .first()
        is not None
    )


def run(db: Session) -> None:
    watchlist = db.query(Watchlist).all()
    if not watchlist:
        return

    tickers = [w.ticker for w in watchlist]
    snapshot = get_snapshot(tickers)

    candidates = [
        t for t in tickers
        if snapshot.get(t, {}).get("day_change_pct", 0) <= _DAY_DROP_THRESHOLD
    ]

    for ticker in candidates:
        if _already_alerted(db, ticker):
            continue

        data = snapshot[ticker]
        news = get_recent_news(ticker)
        history = get_price_history(ticker, days=90)

        recent_closes = [h["close"] for h in history[-20:]] if history else []
        high_20d = max(recent_closes) if recent_closes else 0
        low_20d = min(recent_closes) if recent_closes else 0

        news_lines = "\n".join(f"- {n['title']}" for n in news) if news else "No recent news."
        prompt = (
            f"{ticker} is down {data['day_change_pct']:.1f}% today. "
            f"Current price: ${data['price']:.2f}. "
            f"20-day range: ${low_20d:.2f} – ${high_20d:.2f}.\n"
            f"Recent headlines:\n{news_lines}\n\n"
            "Is this a good buy opportunity? Answer YES or NO, then explain in 2 sentences."
        )
        advice = analyze(prompt)

        if not advice.upper().startswith("YES"):
            continue

        msg = (
            f"<b>BUY SIGNAL — {ticker}</b>\n\n"
            f"Down {data['day_change_pct']:.1f}% today | Price: ${data['price']:.2f}\n\n"
            f"{advice}"
        )
        send_message(msg)
        db.add(Notification(ticker=ticker, type="BUY", message=msg))
        db.commit()
