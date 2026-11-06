import logging


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
