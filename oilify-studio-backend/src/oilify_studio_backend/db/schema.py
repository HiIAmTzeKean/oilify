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
    short_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    long_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prices: Mapped[list[Price]] = relationship(back_populates="ticker")


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("ticker_id", "price_at", name="uq_price_ticker_price_at"),)

    id: Mapped[int] = mapped_column(
        Integer,
        Sequence("prices_id_seq"),
        primary_key=True,
        autoincrement=True,
    )
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False)
    price_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
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


class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"
    __table_args__ = (
        UniqueConstraint(
            "ticker_id",
            "date",
            "name",
            "window_size",
            name="uq_indicator_ticker_date_name_window",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        Sequence("technical_indicators_id_seq"),
        primary_key=True,
        autoincrement=True,
    )
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    window_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    ticker: Mapped[Tickers] = relationship()


class HistoricalVolatility(Base):
    __tablename__ = "historical_volatility"
    __table_args__ = (
        UniqueConstraint(
            "ticker_id",
            "date",
            "window_size",
            name="uq_volatility_ticker_date_window",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        Sequence("historical_volatility_id_seq"),
        primary_key=True,
        autoincrement=True,
    )
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    window_size: Mapped[int] = mapped_column(Integer, nullable=False)
    annualization_factor: Mapped[int] = mapped_column(Integer, nullable=False, default=252)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    ticker: Mapped[Tickers] = relationship()