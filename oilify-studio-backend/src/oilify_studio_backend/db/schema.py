from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Tickers(Base):
    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(
        Integer,
        Sequence("tickers_id_seq"),
        primary_key=True,
        autoincrement=True,
    )
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    prices: Mapped[list[Price]] = relationship(back_populates="ticker")


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("ticker_id", "price_date", name="uq_price_ticker_date"),)

    id: Mapped[int] = mapped_column(
        Integer,
        Sequence("prices_id_seq"),
        primary_key=True,
        autoincrement=True,
    )
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False, default=lambda: date.today())
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="yahoo_finance")
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    ticker: Mapped[Tickers] = relationship(back_populates="prices")