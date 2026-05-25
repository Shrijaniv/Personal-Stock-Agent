from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionIn(BaseModel):
    ticker: str
    action: str  # BUY or SELL
    price: float
    shares: float


@router.get("/")
def list_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).order_by(Transaction.date.desc()).all()


@router.post("/", status_code=201)
def record_transaction(body: TransactionIn, db: Session = Depends(get_db)):
    txn = Transaction(
        ticker=body.ticker.upper(),
        action=body.action.upper(),
        price=body.price,
        shares=body.shares,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn
