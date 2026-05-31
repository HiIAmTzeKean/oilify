import json
import logging as logger
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from recnexteval.registries import ALGORITHM_REGISTRY
from sqlalchemy.orm import Session

from ..db.connection import get_db
from ..db.schema import StreamAlgorithm, StreamJob, StreamUser
from ..schemas.stream import (
    AddAlgorithmsRequest,
    AddAlgorithmsResponse,
    CreateStreamRequest,
    CreateStreamResponse,
)
from ..services.auth import get_current_username

logger = logger.getLogger(__name__)


def create_stream_router() -> APIRouter:
    router = APIRouter(prefix="/stream", tags=["stream"])

    @router.post("/create_stream", response_model=CreateStreamResponse)
    def create_stream(
        request: CreateStreamRequest,
        db: Session = Depends(get_db),
        current_username: str = Depends(get_current_username),
    ) -> CreateStreamResponse:
        logger.info(f"Creating stream job for user {current_username} with request: {request}")
        # Get user from database
        user = db.query(StreamUser).filter(StreamUser.username == current_username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Parse timestamp
        try:
            timestamp_split_start = datetime.fromisoformat(request.timestamp_split_start.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp format")

        # Check for duplicate job name
        existing_job = db.query(StreamJob).filter(StreamJob.name == request.name).first()
        if existing_job:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A stream job with the name '{request.name}' already exists. Please choose a different name.",
            )

        # Create stream job
        stream_job = StreamJob(
            name=request.name,
            description=request.description,
            dataset=request.dataset,
            top_k=request.top_k,
            metrics=request.metrics,
            timestamp_split_start=timestamp_split_start,
            window_size=request.window_size,
            user_id=user.id,
        )

        db.add(stream_job)
        db.commit()
        db.refresh(stream_job)

        logger.info(f"Created stream job {stream_job.id} for user {current_username}")
        return CreateStreamResponse(stream_job_id=stream_job.id, status=stream_job.status)

    @router.get("/list_available")
    def list_available_streams(
        db: Session = Depends(get_db), current_username: str = Depends(get_current_username),
    ) -> list[dict]:
        # Get user from database
        user = db.query(StreamUser).filter(StreamUser.username == current_username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get stream jobs that haven't started yet (available for configuration/running)
        stream_jobs = (
            db.query(StreamJob)
            .filter(StreamJob.user_id == user.id, StreamJob.started_at.is_(None))
            .all()
        )

        result = []
        for job in stream_jobs:
            # Get algorithms for this stream job
            stream_algorithms = db.query(StreamAlgorithm).filter(StreamAlgorithm.stream_job_id == job.id).all()

            # Get algorithm details from registry
            algorithms = []
            registered_algorithms = ALGORITHM_REGISTRY.get_registered_keys()
            for sa in stream_algorithms:
                if sa.algorithm_name in registered_algorithms:
                    algorithms.append(
                        {
                            "id": sa.id,
                            "name": sa.algorithm_name,
                            "description": f"Recommendation algorithm: {sa.algorithm_name}",
                            "category": "Recommendation",
                            "params": sa.parameters,
                        }
                    )

            result.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "description": job.description,
                    "status": job.status,
                    "dataset": job.dataset,
                    "top_k": job.top_k,
                    "metrics": job.metrics,
                    "window_size": job.window_size,
                    "created_at": job.created_at.isoformat(),
                    "algorithms": algorithms,
                }
            )

        return result

    @router.get("/list_all")
    def list_all_streams(
        db: Session = Depends(get_db), current_username: str = Depends(get_current_username)
    ) -> list[dict]:
        # Get user from database
        user = db.query(StreamUser).filter(StreamUser.username == current_username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get all stream jobs for the user
        stream_jobs = db.query(StreamJob).filter(StreamJob.user_id == user.id).all()

        result = []
        for job in stream_jobs:
            # Get algorithms for this stream job
            stream_algorithms = db.query(StreamAlgorithm).filter(StreamAlgorithm.stream_job_id == job.id).all()

            # Get algorithm details from registry
            algorithms = []
            registered_algorithms = ALGORITHM_REGISTRY.get_registered_keys()
            for sa in stream_algorithms:
                if sa.algorithm_name in registered_algorithms:
                    algorithms.append(
                        {
                            "id": sa.id,
                            "name": sa.algorithm_name,
                            "description": f"Recommendation algorithm: {sa.algorithm_name}",
                            "category": "Recommendation",
                            "params": sa.parameters,
                        }
                    )

            result.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "description": job.description,
                    "status": job.status,
                    "dataset": job.dataset,
                    "top_k": job.top_k,
                    "metrics": job.metrics,
                    "window_size": job.window_size,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error_message": job.error_message,
                    "algorithms": algorithms,
                }
            )

        return result

    @router.post("/{stream_job_id}/add_algorithms", response_model=AddAlgorithmsResponse)
    def add_algorithms_to_stream(
        stream_job_id: int,
        request: AddAlgorithmsRequest,
        db: Session = Depends(get_db),
        current_username: str = Depends(get_current_username),
    ) -> AddAlgorithmsResponse:
        # Get user from database
        user = db.query(StreamUser).filter(StreamUser.username == current_username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get stream job
        stream_job = db.query(StreamJob).filter(StreamJob.id == stream_job_id, StreamJob.user_id == user.id).first()
        if not stream_job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream job not found")
        if stream_job.started_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stream job has already started and cannot have algorithms added",
            )

        for algo in request.algorithms:
            if algo.name not in ALGORITHM_REGISTRY:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Algorithm {algo.name} not found in recnexteval registry",
                )

        # Upsert StreamAlgorithm entries: update by id if provided, else insert new
        for algo in request.algorithms:
            if algo.id is not None:
                existing = db.query(StreamAlgorithm).filter(
                    StreamAlgorithm.id == algo.id,
                    StreamAlgorithm.stream_job_id == stream_job_id,
                ).first()
                if not existing:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Algorithm with id {algo.id} not found in stream job {stream_job_id}",
                    )
                existing.parameters = json.dumps(algo.params)
            else:
                stream_algorithm = StreamAlgorithm(
                    stream_job_id=stream_job_id,
                    algorithm_name=algo.name,
                    parameters=json.dumps(algo.params),
                    algorithm_uuid=uuid.uuid5(
                        uuid.NAMESPACE_OID,
                        f"{algo.name}:{datetime.now(UTC).isoformat()}",
                    ),
                )
                db.add(stream_algorithm)

        db.commit()

        logger.info(f"Added {len(request.algorithms)} algorithms to stream job {stream_job_id}")
        return AddAlgorithmsResponse(
            message=f"Successfully added {len(request.algorithms)} algorithms",
            stream_job_id=stream_job_id,
            status=stream_job.status,
        )

    @router.delete("/{stream_job_id}")
    def delete_stream_job(
        stream_job_id: int,
        db: Session = Depends(get_db),
        current_username: str = Depends(get_current_username),
    ) -> dict:
        # Get user from database
        user = db.query(StreamUser).filter(StreamUser.username == current_username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get stream job
        stream_job = db.query(StreamJob).filter(StreamJob.id == stream_job_id, StreamJob.user_id == user.id).first()
        if not stream_job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream job not found")

        # Delete the stream job (cascade will handle related records)
        db.delete(stream_job)
        db.commit()

        logger.info(f"Deleted stream job {stream_job_id} for user {current_username}")
        return {"message": f"Stream job {stream_job_id} deleted successfully"}

    @router.delete("/{stream_job_id}/remove_algorithm/{algorithm_id}")
    def delete_algorithm_from_stream(
        stream_job_id: int,
        algorithm_id: int,
        db: Session = Depends(get_db),
        current_username: str = Depends(get_current_username),
    ) -> dict:
        # Get user from database
        user = db.query(StreamUser).filter(StreamUser.username == current_username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get stream job
        stream_job = db.query(StreamJob).filter(StreamJob.id == stream_job_id, StreamJob.user_id == user.id).first()
        if not stream_job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream job not found")
        if stream_job.started_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stream job has already started and cannot have algorithms removed",
            )

        # Get the StreamAlgorithm entry by id and ensure it belongs to the stream job
        stream_algorithm = db.query(StreamAlgorithm).filter(
            StreamAlgorithm.id == algorithm_id,
            StreamAlgorithm.stream_job_id == stream_job_id
        ).first()
        if not stream_algorithm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Algorithm with id {algorithm_id} not found in stream job {stream_job_id}",
            )

        # Delete the StreamAlgorithm entry
        db.delete(stream_algorithm)
        db.commit()

        logger.info(f"Deleted algorithm {stream_algorithm.algorithm_name} (id: {algorithm_id}) from stream job {stream_job_id}")
        return {"message": f"Algorithm {stream_algorithm.algorithm_name} deleted successfully from stream job {stream_job_id}"}

    return router
