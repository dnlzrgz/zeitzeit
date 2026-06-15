import time

import structlog
from fastapi import Request

logger = structlog.get_logger()


async def log_requests(request: Request, call_next):
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "unhandled_exception",
            method=request.method,
            path=request.url.path,
        )
        raise

    duration = time.perf_counter() - start
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        response_time=f"{duration:.3f}s",
    )

    return response
