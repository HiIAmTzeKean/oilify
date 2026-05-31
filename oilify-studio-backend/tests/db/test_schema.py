"""Tests for ORM model behaviour defined in db/schema.py."""

import json
import uuid
from datetime import datetime, timezone

import pytest

from recnexteval_studio_backend.db.schema import StreamJob, StreamUser


class TestStreamJobStatus:
    """The `status` property must derive the correct lifecycle state from timestamps."""

    def test_created_when_no_algorithms_and_no_timestamps(self, db, stream_user):
        job = StreamJob(
            name=f"job-{uuid.uuid4().hex}",
            dataset="movielens",
            top_k=10,
            metrics=json.dumps(["ndcg"]),
            timestamp_split_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            window_size=7,
            user_id=stream_user.id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        assert job.status == "created"

    def test_ready_when_algorithms_present_and_not_started(self, db, stream_job_factory):
        job = stream_job_factory(algorithms=[{"name": "als", "uuid": uuid.uuid4()}])
        assert job.status == "ready"

    def test_running_when_started_but_not_completed(self, db, stream_job_factory):
        job = stream_job_factory()
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        assert job.status == "running"

    def test_completed_when_completed_at_set_and_no_error(self, db, stream_job_factory):
        job = stream_job_factory()
        job.started_at = datetime.now(timezone.utc)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        assert job.status == "completed"

    def test_failed_when_completed_at_set_and_error_message_non_null(self, db, stream_job_factory):
        job = stream_job_factory()
        job.started_at = datetime.now(timezone.utc)
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = "Dataset unavailable"
        db.commit()
        db.refresh(job)
        assert job.status == "failed"

    def test_completed_takes_priority_over_running(self, db, stream_job_factory):
        """completed_at check must short-circuit before the started_at check."""
        job = stream_job_factory()
        job.started_at = datetime.now(timezone.utc)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        assert job.status == "completed"

    def test_failed_requires_both_completed_at_and_error_message(self, db, stream_job_factory):
        """error_message alone (without completed_at) must not produce 'failed'."""
        job = stream_job_factory()
        job.started_at = datetime.now(timezone.utc)
        job.error_message = "orphaned error"
        db.commit()
        db.refresh(job)
        assert job.status != "failed"


class TestStreamUserModel:
    """Constraint and relationship checks for StreamUser."""

    def test_email_is_optional(self, db):
        user = StreamUser(username=f"nomail-{uuid.uuid4().hex[:8]}", password="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        assert user.email is None

    def test_username_uniqueness_constraint(self, db):
        name = f"dup-{uuid.uuid4().hex[:8]}"
        db.add(StreamUser(username=name, password="hash1"))
        db.commit()
        db.add(StreamUser(username=name, password="hash2"))
        with pytest.raises(Exception):
            db.commit()
        db.rollback()

    def test_user_has_streams_relationship(self, db, stream_user, stream_job_factory):
        job = stream_job_factory()
        db.refresh(stream_user)
        assert any(j.id == job.id for j in stream_user.streams)

    def test_stream_job_back_populates_user(self, db, stream_job_factory):
        job = stream_job_factory()
        db.refresh(job)
        assert job.stream_user is not None
        assert job.stream_user.id == job.user_id


class TestStreamJobRelationships:
    """Cascade and relationship behaviour for StreamJob."""

    def test_algorithms_relationship_populated(self, db, stream_job_factory):
        job = stream_job_factory(algorithms=[{"name": "als", "uuid": uuid.uuid4()}])
        db.refresh(job)
        assert len(job.stream_algorithms) == 1
        assert job.stream_algorithms[0].algorithm_name == "als"

    def test_multiple_algorithms_stored(self, db, stream_job_factory):
        algos = [
            {"name": "als", "uuid": uuid.uuid4()},
            {"name": "svd", "uuid": uuid.uuid4()},
        ]
        job = stream_job_factory(algorithms=algos)
        db.refresh(job)
        names = {sa.algorithm_name for sa in job.stream_algorithms}
        assert names == {"als", "svd"}
