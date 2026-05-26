from fastapi import APIRouter

from app.src.auth.router import router as auth_router
from app.src.entries.router import router as time_entries_router
from app.src.projects.router import router as projects_router
from app.src.tags.router import router as tags_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(tags_router)
api_router.include_router(projects_router)
api_router.include_router(time_entries_router)
