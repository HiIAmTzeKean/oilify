from sqlalchemy import select

from oilify_studio_backend.db.connection import get_database_manager
from oilify_studio_backend.db.schema import Tickers


def seed_initial_tickers() -> None:
    """Seed the database with default tickers if the tickers table is empty.

    This function is idempotent: if there are already tickers present it does nothing.
    """
    db_manager = get_database_manager()
    session = db_manager.get_session()
    try:
        stmt = select(Tickers)
        existing = session.execute(stmt).first()
        if existing:
            return

        tickers = [
            Tickers(symbol="WTI", ticker="CL=F"),
            Tickers(symbol="BRENT", ticker="BZ=F"),
        ]
        session.add_all(tickers)
        session.commit()
    finally:
        session.close()