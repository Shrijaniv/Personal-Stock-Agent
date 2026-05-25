from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
def list_notifications(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Notification).order_by(Notification.sent_at.desc()).limit(limit).all()
