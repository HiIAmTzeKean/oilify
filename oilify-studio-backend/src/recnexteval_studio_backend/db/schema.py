"""
Database schema for recnexteval Studio.

Workflow:
1. User creates StreamJob with parameters → status = "created" (no algorithms, no timestamps)
2. User adds algorithms to StreamJob via StreamAlgorithm table → status = "ready" (has algorithms, no timestamps)
3. User runs StreamJob → status = "running" (started_at set, completed_at NULL)
4. Evaluation completes successfully → status = "completed" (completed_at set, error_message NULL)
5. Evaluation fails → status = "failed" (completed_at set, error_message non-NULL)

Status is derived from timestamps and error_message field.
"""

from datetime import UTC, datetime

from sqlalchemy import ARRAY, Column, DateTime, Float, ForeignKey, Integer, Sequence, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class StreamUser(Base):
    __tablename__ = "stream_user"
    id = Column(Integer, Sequence("stream_user_id_seq"), primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    streams = relationship("StreamJob", back_populates="stream_user")


class StreamJob(Base):
    __tablename__ = "stream_job"
    id = Column(Integer, Sequence("stream_job_id_seq"), primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    started_at = Column(DateTime, nullable=True)  # When execution started
    completed_at = Column(DateTime, nullable=True)  # When execution completed
    error_message = Column(Text, nullable=True)  # NULL = success, non-NULL = failure

    # Stream configuration
    dataset = Column(String, nullable=False)
    top_k = Column(Integer, nullable=False)
    metrics = Column(ARRAY(String), nullable=False)
    timestamp_split_start = Column(DateTime, nullable=False)
    window_size = Column(Integer, nullable=False)

    # Foreign key
    user_id = Column(Integer, ForeignKey("stream_user.id"), nullable=False)

    # Relationships
    stream_user = relationship("StreamUser", back_populates="streams")
    stream_algorithms = relationship("StreamAlgorithm", back_populates="stream_job", cascade="all, delete-orphan")
    macro_evaluations = relationship("MacroEvaluationResult", back_populates="stream_job", cascade="all, delete-orphan")
    micro_evaluations = relationship("MicroEvaluationResult", back_populates="stream_job", cascade="all, delete-orphan")
    window_evaluations = relationship("WindowEvaluationResult", back_populates="stream_job", cascade="all, delete-orphan")
    user_evaluations = relationship("UserEvaluationResult", back_populates="stream_job", cascade="all, delete-orphan")

    @property
    def status(self) -> str:
        """Derive status from timestamps and error_message"""
        if self.completed_at:
            return "failed" if self.error_message else "completed"
        elif self.started_at:
            return "running"
        elif self.stream_algorithms:  # Has algorithms added
            return "ready"
        else:
            return "created"


class StreamAlgorithm(Base):
    __tablename__ = "stream_algorithm"
    id = Column(Integer, Sequence("stream_algorithm_id_seq"), primary_key=True, autoincrement=True)
    stream_job_id = Column(Integer, ForeignKey("stream_job.id"), nullable=False)
    algorithm_name = Column(String, nullable=False)  # Algorithm name from recnexteval registry
    algorithm_uuid = Column(UUID(as_uuid=True), nullable=True)

    # Algorithm-specific configuration
    parameters = Column(Text)  # JSON string of algorithm parameters
    added_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    stream_job = relationship("StreamJob", back_populates="stream_algorithms")
    macro_evaluations = relationship("MacroEvaluationResult", back_populates="stream_algorithm", cascade="all, delete-orphan")
    micro_evaluations = relationship("MicroEvaluationResult", back_populates="stream_algorithm", cascade="all, delete-orphan")
    window_evaluations = relationship("WindowEvaluationResult", back_populates="stream_algorithm", cascade="all, delete-orphan")
    user_evaluations = relationship("UserEvaluationResult", back_populates="stream_algorithm", cascade="all, delete-orphan")


class MacroEvaluationResult(Base):
    __tablename__ = "macro_evaluation_result"
    id = Column(Integer, Sequence("macro_evaluation_result_id_seq"), primary_key=True, autoincrement=True)
    stream_job_id = Column(Integer, ForeignKey("stream_job.id"), nullable=False)
    stream_algorithm_id = Column(Integer, ForeignKey("stream_algorithm.id"), nullable=False)

    # Macro evaluation details
    metric = Column(String, nullable=False)
    macro_score = Column(Float, nullable=False)
    num_window = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    # Relationships
    stream_job = relationship("StreamJob", back_populates="macro_evaluations")
    stream_algorithm = relationship("StreamAlgorithm", back_populates="macro_evaluations")


class MicroEvaluationResult(Base):
    __tablename__ = "micro_evaluation_result"
    id = Column(Integer, Sequence("micro_evaluation_result_id_seq"), primary_key=True, autoincrement=True)
    stream_job_id = Column(Integer, ForeignKey("stream_job.id"), nullable=False)
    stream_algorithm_id = Column(Integer, ForeignKey("stream_algorithm.id"), nullable=False)

    # Micro evaluation details - add specific fields as needed
    metric = Column(String, nullable=False)
    micro_score = Column(Float, nullable=False)
    num_user = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    stream_job = relationship("StreamJob", back_populates="micro_evaluations")
    stream_algorithm = relationship("StreamAlgorithm", back_populates="micro_evaluations")


class WindowEvaluationResult(Base):
    __tablename__ = "window_evaluation_result"
    id = Column(Integer, Sequence("window_evaluation_result_id_seq"), primary_key=True, autoincrement=True)
    stream_job_id = Column(Integer, ForeignKey("stream_job.id"), nullable=False)
    stream_algorithm_id = Column(Integer, ForeignKey("stream_algorithm.id"), nullable=False)

    # Window evaluation details - add specific fields as needed
    metric = Column(String, nullable=False)
    window_score = Column(Float, nullable=False)
    num_user = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    stream_job = relationship("StreamJob", back_populates="window_evaluations")
    stream_algorithm = relationship("StreamAlgorithm", back_populates="window_evaluations")


class UserEvaluationResult(Base):
    __tablename__ = "user_evaluation_result"
    id = Column(Integer, Sequence("user_evaluation_result_id_seq"), primary_key=True, autoincrement=True)
    stream_job_id = Column(Integer, ForeignKey("stream_job.id"), nullable=False)
    stream_algorithm_id = Column(Integer, ForeignKey("stream_algorithm.id"), nullable=False)

    # User evaluation details - add specific fields as needed
    metric = Column(String, nullable=False)
    user_score = Column(Float, nullable=False)
    user_id = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    stream_job = relationship("StreamJob", back_populates="user_evaluations")
    stream_algorithm = relationship("StreamAlgorithm", back_populates="user_evaluations")
