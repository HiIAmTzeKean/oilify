import json

from sqlalchemy import select

from recnexteval_studio_backend.db.connection import get_database_manager
from recnexteval_studio_backend.db.schema import StreamAlgorithm, StreamJob, StreamUser
from recnexteval_studio_backend.services.auth import hash_password


def seed_initial_users() -> None:
    """Seed the database with three default users if the user table is empty.

    This function is idempotent: if there are already users present it does nothing.
    """
    db_manager = get_database_manager()
    session = db_manager.get_session()
    try:
        stmt = select(StreamUser)
        existing = session.execute(stmt).first()
        if existing:
            return

        users = [
            StreamUser(username="admin", email="admin@example.com", password=hash_password("admin")),
            StreamUser(username="alice", email="alice@example.com", password=hash_password("alice")),
            StreamUser(username="bob", email="bob@example.com", password=hash_password("bob")),
            StreamUser(username="carol", email="carol@example.com", password=hash_password("carol")),
        ]
        session.add_all(users)
        session.commit()
    finally:
        session.close()

def seed_inital_stream_jobs() -> None:
    """Seed the database with initial stream jobs for testing purposes."""

    db_manager = get_database_manager()
    session = db_manager.get_session()
    try:
        stmt = select(StreamJob)
        existing = session.execute(stmt).first()
        if existing:
            return

        StreamJob1 = StreamJob(
            name="Test Stream Job 1",
            description="This is a test stream job for user alice.",
            dataset="MovieLens100K",
            top_k=5,
            metrics=["PrecisionK", "RecallK"],
            timestamp_split_start="1998-02-05 00:00:00",
            window_size=2592000,
            user_id=1,
        )
        StreamAlgo1 = StreamAlgorithm(
            algorithm_name="ItemKNNIncremental",
            parameters=json.dumps({"K": 10, "pad_with_popularity": True}),
            algorithm_uuid='d8161a65-e473-5257-889d-ac256d8175cd',
            stream_job_id=1,
        )
        session.add_all([StreamJob1, StreamAlgo1])
    finally:
        session.close()
