from datetime import datetime, timedelta, timezone
from uuid import UUID

from faker import Faker
from sqlmodel import Session

from app.models import (
    Project,
    ProjectCreate,
    Tag,
    TagCreate,
    TimeEntry,
    TimeEntryCreate,
)
from app.src.projects import services as project_services
from app.src.tags import services as tag_services
from app.src.entries import services as entry_services

_faker = Faker()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _create_tag(
    session: Session,
    user_id: UUID,
    name: str | None = None,
) -> Tag:
    return tag_services.create(
        session=session,
        user_id=user_id,
        tag_in=TagCreate(
            name=name or _faker.unique.word(),
        ),
    )


def _create_project(
    session: Session,
    user_id: UUID,
    name: str | None = None,
    color: str | None = None,
) -> Project:
    return project_services.create(
        session=session,
        user_id=user_id,
        project_in=ProjectCreate(
            name=name or _faker.unique.word(),
            color=color or _faker.hex_color(),
        ),
    )


_UNSET = object()


def _create_time_entry(
    session: Session,
    user_id: UUID,
    description: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = _UNSET,  # type: ignore[assignment]
    project_id: UUID | None = None,
    tag_ids: list[UUID] | None = None,
) -> TimeEntry:
    start = start_time or _now()
    return entry_services.create(
        session=session,
        user_id=user_id,
        time_entry_in=TimeEntryCreate(
            description=description or _faker.sentence(),
            start_time=start,
            end_time=start + timedelta(minutes=30) if end_time is _UNSET else end_time,
            project_id=project_id,
            tag_ids=tag_ids or [],
        ),
    )
