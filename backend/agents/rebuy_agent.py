from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import Transaction, Notification
from services.claude_client import analyze
from services.telegram import send_message

_DEDUP_WINDOW = timedelta(hours=1)


def _already_alerted(db: Session, ticker: str) -> bool:
    cutoff = datetime.now(timezone.utc) - _DEDUP_WINDOW
    return (
        db.query(Notification)
        .filter(
            Notification.ticker == ticker,
            Notification.type == "REBUY",
            Notification.sent_at >= cutoff,
        )
        .first()
        is not None
    )


def run(db: Session, snapshot: dict[str, dict]) -> None:
    """Check if any previously sold ticker has dropped 10% below sell price."""
    latest_sells = (
        db.query(Transaction.ticker, func.max(Transaction.date).label("last_date"))
        .filter(Transaction.action == "SELL")
        .group_by(Transaction.ticker)
        .subquery()
    )
    sell_txns = (
        db.query(Transaction)
        .join(latest_sells, (Transaction.ticker == latest_sells.c.ticker) & (Transaction.date == latest_sells.c.last_date))
        .all()
    )

    for txn in sell_txns:
        ticker = txn.ticker
        data = snapshot.get(ticker)
        if not data or not data["price"]:
            continue

        current_price = data["price"]
        if current_price <= txn.price * 0.90:
            if _already_alerted(db, ticker):
                continue

            pct_drop = ((txn.price - current_price) / txn.price) * 100
            prompt = (
                f"{ticker} was sold at ${txn.price:.2f}. "
                f"It has since dropped {pct_drop:.1f}% to ${current_price:.2f}. "
                "Is this a good re-entry point? Brief answer."
            )
            advice = analyze(prompt)
            msg = (
                f"<b>REBUY SIGNAL — {ticker}</b>\n\n"
                f"Sold at: ${txn.price:.2f} | Now: ${current_price:.2f} ({pct_drop:.1f}% drop)\n\n"
                f"{advice}"
            )
            send_message(msg)
            db.add(Notification(ticker=ticker, type="REBUY", message=msg))
            db.commit()
