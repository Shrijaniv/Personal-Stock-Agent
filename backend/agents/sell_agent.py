from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models import Holding, Notification
from services.market_data import get_snapshot
from services.claude_client import analyze
from services.telegram import send_message

_DEDUP_WINDOW = timedelta(hours=1)


def _already_alerted(db: Session, ticker: str, alert_type: str) -> bool:
    cutoff = datetime.now(timezone.utc) - _DEDUP_WINDOW
    return (
        db.query(Notification)
        .filter(
            Notification.ticker == ticker,
            Notification.type == alert_type,
            Notification.sent_at >= cutoff,
        )
        .first()
        is not None
    )


def run(db: Session, snapshot: dict[str, dict] | None = None) -> dict[str, dict]:
    """Run sell-signal checks. Returns the snapshot so rebuy_agent can reuse it."""
    holdings = db.query(Holding).all()
    if not holdings:
        return {}

    tickers = [h.ticker for h in holdings]
    if snapshot is None:
        snapshot = get_snapshot(tickers)

    for holding in holdings:
        ticker = holding.ticker
        data = snapshot.get(ticker)
        if not data or not data["price"]:
            continue

        ath = holding.cached_ath
        if not ath:
            continue

        current_price = data["price"]
        if current_price >= ath * 0.99:
            if _already_alerted(db, ticker, "SELL"):
                continue

            prompt = (
                f"{ticker} is near its all-time high of ${ath:.2f}. "
                f"Current price: ${current_price:.2f} "
                f"(today: {data['day_change_pct']:+.2f}%). "
                "Should I consider selling? Give a brief recommendation."
            )
            advice = analyze(prompt)
            msg = f"<b>SELL SIGNAL — {ticker}</b>\n\nPrice: ${current_price:.2f} (ATH: ${ath:.2f})\n\n{advice}"
            send_message(msg)
            db.add(Notification(ticker=ticker, type="SELL", message=msg))
            db.commit()

    return snapshot
