from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Watchlist

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistIn(BaseModel):
    ticker: str
    notes: str | None = None


@router.get("/")
def list_watchlist(db: Session = Depends(get_db)):
    return db.query(Watchlist).all()


@router.post("/", status_code=201)
def add_to_watchlist(body: WatchlistIn, db: Session = Depends(get_db)):
    ticker = body.ticker.upper()
    if db.query(Watchlist).filter(Watchlist.ticker == ticker).first():
        raise HTTPException(400, f"{ticker} already on watchlist")
    item = Watchlist(ticker=ticker, notes=body.notes)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{ticker}", status_code=204)
def remove_from_watchlist(ticker: str, db: Session = Depends(get_db)):
    item = db.query(Watchlist).filter(Watchlist.ticker == ticker.upper()).first()
    if not item:
        raise HTTPException(404, f"{ticker} not found")
    db.delete(item)
    db.commit()
