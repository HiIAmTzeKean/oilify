"""bootstrap oilify schema

Revision ID: 0001_bootstrap_schema
Revises: 
Create Date: 2026-06-01 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_bootstrap_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_table_names() -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return set(inspector.get_table_names())


def _existing_column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _create_tickers_table() -> None:
    op.create_table(
        "tickers",
        sa.Column("id", sa.Integer(), sa.Sequence("tickers_id_seq"), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("short_name", sa.String(length=128), nullable=True),
        sa.Column("long_name", sa.String(length=128), nullable=True),
        sa.UniqueConstraint("symbol", name="uq_tickers_symbol"),
    )


def _create_prices_table() -> None:
    op.create_table(
        "prices",
        sa.Column("id", sa.Integer(), sa.Sequence("prices_id_seq"), primary_key=True, autoincrement=True),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id"), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("ticker_id", "price_date", name="uq_price_ticker_date"),
    )


def _create_technical_indicators_table() -> None:
    op.create_table(
        "technical_indicators",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Sequence("technical_indicators_id_seq"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id"), nullable=False),
        sa.Column("indicator_date", sa.Date(), nullable=False),
        sa.Column("indicator_name", sa.String(length=32), nullable=False),
        sa.Column("indicator_value", sa.Float(), nullable=False),
        sa.Column("window_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("ticker_id", "indicator_date", "indicator_name", name="uq_indicator_ticker_date_name"),
    )


def _create_historical_volatility_table() -> None:
    op.create_table(
        "historical_volatility",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Sequence("historical_volatility_id_seq"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id"), nullable=False),
        sa.Column("volatility_date", sa.Date(), nullable=False),
        sa.Column("annualized_volatility", sa.Float(), nullable=False),
        sa.Column("window_size", sa.Integer(), nullable=False),
        sa.Column("annualization_factor", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("ticker_id", "volatility_date", "window_size", name="uq_volatility_ticker_date_window"),
    )


def upgrade() -> None:
    table_names = _existing_table_names()

    if "tickers" not in table_names:
        _create_tickers_table()

    if "prices" not in table_names:
        _create_prices_table()
    else:
        price_columns = _existing_column_names("prices")
        if "price_usd" in price_columns and "price" not in price_columns:
            with op.batch_alter_table("prices") as batch_op:
                batch_op.alter_column("price_usd", new_column_name="price")

    if "technical_indicators" not in table_names:
        _create_technical_indicators_table()

    if "historical_volatility" not in table_names:
        _create_historical_volatility_table()


def downgrade() -> None:
    table_names = _existing_table_names()

    if "historical_volatility" in table_names:
        op.drop_table("historical_volatility")

    if "technical_indicators" in table_names:
        op.drop_table("technical_indicators")

    if "prices" in table_names:
        price_columns = _existing_column_names("prices")
        if "price" in price_columns and "price_usd" not in price_columns:
            with op.batch_alter_table("prices") as batch_op:
                batch_op.alter_column("price", new_column_name="price_usd")

        op.drop_table("prices")

    if "tickers" in table_names:
        op.drop_table("tickers")
