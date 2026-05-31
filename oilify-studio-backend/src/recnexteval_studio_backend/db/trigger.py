from sqlalchemy import text
from sqlalchemy.orm import Session


def deduplicate_stock_price(session: Session) -> None:
    dedup_query = text("""
        INSERT INTO stock_price (stock_ticker, datetime, open, high, low, close, volume)
        SELECT stock_ticker, datetime, open, high, low, close, volume
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY stock_ticker, datetime ORDER BY ingest_time DESC) as rn
            FROM raw_stock_price
        )
        WHERE rn = 1
        ON CONFLICT (stock_ticker, datetime) DO UPDATE SET
            open=excluded.open,
            high=excluded.high,
            low=excluded.low,
            close=excluded.close,
            volume=excluded.volume
    """)
    session.execute(dedup_query)
    session.commit()
