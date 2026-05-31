import logging as logger
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from recnexteval_studio_backend.db.connection import get_db
from recnexteval_studio_backend.db.schema import (
    MacroEvaluationResult,
    MicroEvaluationResult,
    StreamAlgorithm,
    StreamJob,
    StreamUser,
    UserEvaluationResult,
    WindowEvaluationResult,
)
from recnexteval_studio_backend.services.auth import get_current_username

from ..services.evaluator import run_evaluation

logger = logger.getLogger(__name__)


def create_evaluator_router() -> APIRouter:
    router = APIRouter(prefix="/evaluator", tags=["evaluator"])

    @router.post("/{stream_job_id}/run")
    async def run_stream_job(
        stream_job_id: int,
        background_tasks: BackgroundTasks,
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
        if not stream_job.stream_algorithms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stream job has no algorithms configured",
            )
        if stream_job.started_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stream job has already started",
            )

        stream_job.started_at = datetime.now(UTC)
        db.commit()

        background_tasks.add_task(run_evaluation, stream_job.id)
        logger.info(f"Started evaluation for stream job {stream_job_id}")
        return {"message": "Stream job started", "status": stream_job.status}

    @router.post("/{stream_job_id}/rerun")
    async def rerun_stream_job(
        stream_job_id: int,
        background_tasks: BackgroundTasks,
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
        if stream_job.completed_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stream job has not completed yet and cannot be rerun",
            )

        # Reset job state for rerun
        stream_job.started_at = datetime.now(UTC)
        stream_job.completed_at = None
        stream_job.error_message = None

        # delete all previous evaluation results associated with this stream job
        db.query(MacroEvaluationResult).filter(MacroEvaluationResult.stream_job_id == stream_job_id).delete()
        db.query(MicroEvaluationResult).filter(MicroEvaluationResult.stream_job_id == stream_job_id).delete()
        db.query(WindowEvaluationResult).filter(WindowEvaluationResult.stream_job_id == stream_job_id).delete()
        db.query(UserEvaluationResult).filter(UserEvaluationResult.stream_job_id == stream_job_id).delete()
        db.commit()

        background_tasks.add_task(run_evaluation, stream_job.id)

        logger.info(f"Started rerunning stream job {stream_job_id}")
        return {"message": "Stream job rerun started", "status": stream_job.status}

    @router.get("/{stream_job_id}/results")
    def get_evaluation_history(
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

        # Get evaluation results from all tables with algorithm names
        macro_results = (
            db.query(MacroEvaluationResult, StreamAlgorithm.algorithm_name)
            .join(StreamAlgorithm, MacroEvaluationResult.stream_algorithm_id == StreamAlgorithm.id)
            .filter(MacroEvaluationResult.stream_job_id == stream_job_id)
            .all()
        )
        micro_results = (
            db.query(MicroEvaluationResult, StreamAlgorithm.algorithm_name)
            .join(StreamAlgorithm, MicroEvaluationResult.stream_algorithm_id == StreamAlgorithm.id)
            .filter(MicroEvaluationResult.stream_job_id == stream_job_id)
            .all()
        )
        window_results = (
            db.query(WindowEvaluationResult, StreamAlgorithm.algorithm_name)
            .join(StreamAlgorithm, WindowEvaluationResult.stream_algorithm_id == StreamAlgorithm.id)
            .filter(WindowEvaluationResult.stream_job_id == stream_job_id)
            .all()
        )
        user_results = (
            db.query(UserEvaluationResult, StreamAlgorithm.algorithm_name)
            .join(StreamAlgorithm, UserEvaluationResult.stream_algorithm_id == StreamAlgorithm.id)
            .filter(UserEvaluationResult.stream_job_id == stream_job_id)
            .all()
        )

        result = {
            "macro": [],
            "micro": [],
            "window": [],
            "user": []
        }

        # Process macro results
        for eval_result, algorithm_name in macro_results:
            result["macro"].append(
                {
                    "id": eval_result.id,
                    "algorithm": algorithm_name,
                    "metric": eval_result.metric,
                    "score": eval_result.macro_score,
                    "num_window": eval_result.num_window,
                }
            )

        # Process micro results
        for eval_result, algorithm_name in micro_results:
            result["micro"].append(
                {
                    "id": eval_result.id,
                    "algorithm": algorithm_name,
                    "metric": eval_result.metric,
                    "score": eval_result.micro_score,
                    "num_user": eval_result.num_user,
                }
            )

        # Process window results
        for eval_result, algorithm_name in window_results:
            result["window"].append(
                {
                    "id": eval_result.id,
                    "algorithm": algorithm_name,
                    "metric": eval_result.metric,
                    "score": eval_result.window_score,
                    "num_user": eval_result.num_user,
                    "timestamp": eval_result.timestamp,
                }
            )

        # Process user results
        for eval_result, algorithm_name in user_results:
            result["user"].append(
                {
                    "id": eval_result.id,
                    "algorithm": algorithm_name,
                    "metric": eval_result.metric,
                    "score": eval_result.user_score,
                    "user_id": eval_result.user_id,
                    "timestamp": eval_result.timestamp,
                }
            )

        return result

    return router
