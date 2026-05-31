import json
import logging as logger
import traceback
from datetime import UTC, datetime

import recnexteval.evaluators
import recnexteval.registries
import recnexteval.settings
from recnexteval.registries import ALGORITHM_REGISTRY

from ..db.connection import get_database_manager
from ..db.schema import StreamJob
from .evaluation.persisters import ResultPersister

logger = logger.getLogger(__name__)


def run_evaluation(stream_job_id: int) -> None:
    db = get_database_manager().get_session()
    try:
        stream_job = db.query(StreamJob).filter(StreamJob.id == stream_job_id).first()
        if not stream_job:
            logger.error(f"Stream job {stream_job_id} not found")
            return

        logger.info(f"Starting evaluation for stream job {stream_job_id}")
        logger.info(
            f"Dataset: {stream_job.dataset}, timestamp_split_start: {stream_job.timestamp_split_start}, window_size: {stream_job.window_size}, top_k: {stream_job.top_k}"
        )

        try:
            dataset_cls = recnexteval.registries.DATASET_REGISTRY.get(stream_job.dataset)
            logger.info(f"Dataset class: {dataset_cls}")
            dataset = dataset_cls()
            logger.info("Loading dataset...")
            data = dataset.load()
            logger.info(f"Dataset loaded successfully. Data type: {type(data)}")
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            raise

        try:
            logger.info("Setting up sliding window...")
            training_t_epoch = stream_job.timestamp_split_start.timestamp()
            setting_window = recnexteval.settings.SlidingWindowSetting(
                training_t=training_t_epoch,
                window_size=stream_job.window_size,
                top_K=stream_job.top_k,
            )
            logger.info("Splitting data...")
            setting_window.split(data)
            logger.info("Window setup completed")
        except Exception as e:
            logger.error(f"Error setting up window: {e}")
            raise

        try:
            logger.info("Building evaluator pipeline...")
            builder = recnexteval.evaluators.EvaluatorPipelineBuilder()
            builder.add_setting(setting_window)
            builder.set_metric_k(stream_job.top_k)

            for metric_name in stream_job.metrics:
                logger.info(f"Adding metric: {metric_name}")
                builder.add_metric(metric_name)

            for sa in stream_job.stream_algorithms:
                logger.info(f"Adding algorithm: {sa.algorithm_name}")
                algorithm_cls = ALGORITHM_REGISTRY.get(sa.algorithm_name)
                if not algorithm_cls:
                    logger.error(f"Algorithm {sa.algorithm_name} not found in recnexteval registry")
                    continue
                params = json.loads(sa.parameters) if sa.parameters else {}
                logger.info(f"Algorithm params: {params}")
                builder.add_algorithm(
                    algorithm=algorithm_cls,
                    params=params,
                    algo_uuid=sa.algorithm_uuid,
                )
            evaluator = builder.build()
            logger.info("Evaluator built successfully")
        except Exception as e:
            logger.error(f"Error building evaluator: {e}")
            raise

        try:
            logger.info("Running evaluator...")
            evaluator.run()
            logger.info("Evaluator run completed successfully")

            logger.info("Saving evaluation results...")
            ResultPersister(db).persist_all(evaluator, stream_job_id)
            logger.info("Evaluation results saved successfully")
        except Exception as e:
            logger.error(f"Error during evaluator.run(): {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise

        stream_job.completed_at = datetime.now(UTC)
        db.commit()
        logger.info(f"Evaluation completed for stream job {stream_job_id}")
    except Exception as e:
        logger.error(f"Error running evaluation for stream job {stream_job_id}: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        stream_job.completed_at = datetime.now(UTC)
        stream_job.error_message = str(e)
        db.commit()
    finally:
        db.close()
