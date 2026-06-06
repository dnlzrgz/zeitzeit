import logging
import time

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send
from uuid_utils import uuid7

logger = logging.getLogger("app.middleware")


class LoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = f"{uuid7()}"
        start_time = time.perf_counter()
        scope["state"]["request_id"] = request_id

        logger.info(
            "Request started | %s %s",
            scope["method"],
            scope["path"],
            extra={
                "request_id": request_id,
                "method": scope["method"],
                "path": scope["path"],
                "client_ip": scope["client"][0] if scope.get("client") else None,
            },
        )

        status_code = 500

        async def send_wrapper(message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = MutableHeaders(scope=message)
                headers.append("X-Request-ID", request_id)

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            log_fn = logger.warning if status_code >= 400 else logger.info
            log_fn(
                "Request completed | %s %s → %d (%.1fms)",
                scope["method"],
                scope["path"],
                status_code,
                duration_ms,
                extra={
                    "request_id": request_id,
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
