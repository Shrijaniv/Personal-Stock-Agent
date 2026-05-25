from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database import Base


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    shares = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    purchase_date = Column(DateTime, server_default=func.now())
    cached_ath = Column(Float, nullable=True)
    ath_updated_at = Column(DateTime, nullable=True)


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    added_date = Column(DateTime, server_default=func.now())
    notes = Column(String, nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    action = Column(String, nullable=False)  # BUY or SELL
    price = Column(Float, nullable=False)
    shares = Column(Float, nullable=False)
    date = Column(DateTime, server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    type = Column(String, nullable=False)  # SELL, BUY, REBUY
    message = Column(String, nullable=False)
    sent_at = Column(DateTime, server_default=func.now())
