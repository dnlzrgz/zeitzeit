from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.settings import settings
from app.src.auth.router import router as auth_router
from app.src.entries.router import router as time_entries_router
from app.src.projects.router import router as projects_router
from app.src.tags.router import router as tags_router


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(tags_router)
api_router.include_router(projects_router)
api_router.include_router(time_entries_router)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
