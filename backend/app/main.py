import logging

import sentry_sdk
from fastapi import APIRouter, FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRoute
from sentry_sdk.integrations.logging import LoggingIntegration
from starlette.middleware.cors import CORSMiddleware

from app.logger import setup_logger
from app.middleware import LoggingMiddleware
from app.settings import settings
from app.src.auth.router import router as auth_router
from app.src.entries.router import router as time_entries_router
from app.src.projects.router import router as projects_router
from app.src.tags.router import router as tags_router
from app.src.users.router import router as users_router

setup_logger()


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DNS:
    sentry_sdk.init(
        dsn=settings.SENTRY_DNS,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profile_session_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=settings.SENTRY_SEND_DEFAULT_PII,
        integrations=[
            LoggingIntegration(
                level=logging.INFO,
                event_level=None,
            )
        ],
    )


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(tags_router)
api_router.include_router(projects_router)
api_router.include_router(time_entries_router)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

app.add_middleware(LoggingMiddleware)


if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.GZIP_ENABLED:
    app.add_middleware(
        GZipMiddleware,
        minimum_size=settings.GZIP_MINIMUM_SIZE,
        compresslevel=settings.GZIP_COMPRESS_LEVEL,
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
