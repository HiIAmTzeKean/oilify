import logging
import sys


def setup_logging() -> None:
    """Set up logging configuration to capture all logs including recnexteval library."""

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.addHandler(console_handler)

    # Make recnexteval logger propagate to root so we capture its logs
    recnexteval_logger = logging.getLogger('recnexteval')
    recnexteval_logger.propagate = True

    # Also ensure our backend logger propagates
    backend_logger = logging.getLogger('recnexteval_studio_backend')
    backend_logger.propagate = True
