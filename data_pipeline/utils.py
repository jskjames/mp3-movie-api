import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def setup_logging(verbose=False):
    """Configure logging for the pipeline."""
    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


def validate_input(filepath):
    """Check whether the input path exists and is a file."""
    if Path(filepath).is_file():
        logger.info(f"Input file validated: {filepath}")
        return True

    logger.error(f"Input file not found: {filepath}")
    return False
