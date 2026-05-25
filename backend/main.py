from contextlib import asynccontextmanager
from datetime import datetime
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz
from fastapi import FastAPI

import database
import models
from database import SessionLocal
import agents.sell_agent as sell_agent
import agents.rebuy_agent as rebuy_agent
import agents.buy_agent as buy_agent
from services.market_data import get_all_time_high
from routers import portfolio, watchlist, transactions, notifications, agents

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ET = pytz.timezone("America/New_York")


def _market_open() -> bool:
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    t = now.time()
    return t >= now.replace(hour=9, minute=30, second=0).time() and t < now.replace(hour=16, minute=0, second=0).time()


def job_price_check() -> None:
    if not _market_open():
        return
    db = SessionLocal()
    try:
        snapshot = sell_agent.run(db)
        rebuy_agent.run(db, snapshot)
        buy_agent.run(db)
    except Exception:
        log.exception("Error in price check job")
    finally:
        db.close()


def job_refresh_ath() -> None:
    """Refresh cached all-time highs for all holdings. Runs daily."""
    from datetime import datetime, timezone
    db = SessionLocal()
    try:
        holdings = db.query(models.Holding).all()
        for holding in holdings:
            try:
                ath = get_all_time_high(holding.ticker)
                holding.cached_ath = ath
                holding.ath_updated_at = datetime.now(timezone.utc)
                log.info("ATH %s: $%.2f", holding.ticker, ath)
            except Exception:
                log.exception("Failed ATH refresh for %s", holding.ticker)
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=database.engine)

    scheduler = BackgroundScheduler(timezone=ET)
    scheduler.add_job(job_price_check, IntervalTrigger(minutes=1), id="price_check")
    scheduler.add_job(job_refresh_ath, CronTrigger(hour=7, minute=0, timezone=ET), id="ath_refresh")
    scheduler.start()
    log.info("Scheduler started — price check every 1 min, ATH refresh daily at 07:00 ET")

    yield

    scheduler.shutdown()


app = FastAPI(title="Personal Stock Agent", lifespan=lifespan)

app.include_router(portfolio.router)
app.include_router(watchlist.router)
app.include_router(transactions.router)
app.include_router(notifications.router)
app.include_router(agents.router)


@app.get("/health")
def health():
    return {"status": "ok"}
