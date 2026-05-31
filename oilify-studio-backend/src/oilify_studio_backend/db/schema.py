from datetime import UTC, date, datetime

from sqlalchemy import Column, Date, DateTime, Float, Integer, Sequence, String, UniqueConstraint
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class OilPriceDaily(Base):
    __tablename__ = "oil_price_daily"
    __table_args__ = (UniqueConstraint("symbol", "price_date", name="uq_oil_price_symbol_date"),)

    id = Column(Integer, Sequence("oil_price_daily_id_seq"), primary_key=True, autoincrement=True)
    symbol = Column(String(16), nullable=False)
    ticker = Column(String(16), nullable=False)
    price_date = Column(Date, nullable=False, default=lambda: date.today())
    price_usd = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="USD")
    source = Column(String(64), nullable=False, default="yahoo_finance")
    fetched_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

class Tickers(Base):
    __tablename__ = "tickers"

    id = Column(Integer, Sequence("tickers_id_seq"), primary_key=True, autoincrement=True)
    symbol = Column(String(16), nullable=False, unique=True)
    ticker = Column(String(16), nullable=False)