from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Holding

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class HoldingIn(BaseModel):
    ticker: str
    shares: float
    purchase_price: float


@router.get("/")
def list_holdings(db: Session = Depends(get_db)):
    return db.query(Holding).all()


@router.post("/", status_code=201)
def add_holding(body: HoldingIn, db: Session = Depends(get_db)):
    ticker = body.ticker.upper()
    if db.query(Holding).filter(Holding.ticker == ticker).first():
        raise HTTPException(400, f"{ticker} already in portfolio")
    holding = Holding(ticker=ticker, shares=body.shares, purchase_price=body.purchase_price)
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


@router.delete("/{ticker}", status_code=204)
def remove_holding(ticker: str, db: Session = Depends(get_db)):
    holding = db.query(Holding).filter(Holding.ticker == ticker.upper()).first()
    if not holding:
        raise HTTPException(404, f"{ticker} not found")
    db.delete(holding)
    db.commit()
