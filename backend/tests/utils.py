from datetime import datetime, timedelta, timezone

from app.models import Project, ProjectCreate, Tag, TagCreate
from app.src.projects import services as project_services
from app.src.tags import services as tag_services


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dt(offset_mins: int = 0) -> datetime:
    return _now() + timedelta(minutes=offset_mins)


def _create_tag(session, user_id, name) -> Tag:
    return tag_services.create(
        session=session,
        user_id=user_id,
        tag_in=TagCreate(name=name),
    )


def _create_project(session, user_id, name, color="#FF0000") -> Project:
    return project_services.create(
        session=session,
        user_id=user_id,
        project_in=ProjectCreate(name=name, color=color),
    )
