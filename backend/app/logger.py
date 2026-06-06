import logging
import sys

from app.settings import settings


def setup_logger() -> None:
    log_level = logging.DEBUG if settings.ENVIRONMENT == "local" else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    logger = logging.getLogger("app")
    logger.setLevel(log_level)

    if not logger.handlers:
        logger.addHandler(handler)

    if settings.ENVIRONMENT != "local":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
