from datetime import timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models import Project, Tag, TimeEntry, TimeEntryCreate, TimeEntryUpdate
from tests.utils import _now


def test_db_enforces_unique_project_name_per_user(session, regular_user):
    project = Project(
        user_id=regular_user.id,
        name="A",
        color="#0000FF",
    )
    session.add(project)
    session.commit()

    duplicated_project = Project(
        user_id=regular_user.id,
        name="A",
        color="#FFFF00",
    )
    session.add(duplicated_project)

    with pytest.raises(IntegrityError):
        session.commit()


def test_db_enforces_unique_tag_name_per_user(session, regular_user):
    tag = Tag(user_id=regular_user.id, name="A")
    session.add(tag)
    session.commit()

    duplicated_tag = Tag(user_id=regular_user.id, name="A")
    session.add(duplicated_tag)

    with pytest.raises(IntegrityError):
        session.commit()


def test_create_time_entry_with_no_end_time_is_valid():
    time_entry = TimeEntryCreate(start_time=_now())
    assert time_entry.end_time is None


def test_create_time_entry_with_end_time_equal_to_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryCreate(start_time=now, end_time=now)


def test_create_time_entry_with_end_time_before_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryCreate(start_time=now + timedelta(minutes=30), end_time=now)


def test_update_end_time_after_start_is_valid():
    now = _now()
    TimeEntryUpdate(start_time=now, end_time=now + timedelta(minutes=30))


def test_update_time_entry_end_time_to_equal_to_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryUpdate(start_time=now, end_time=now)


def test_update_time_entry_end_time_before_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryUpdate(start_time=now + timedelta(minutes=30), end_time=now)


def test_db_enforces_one_running_time_entry_per_user(session, regular_user):
    now = _now()

    time_entry = TimeEntry(
        user_id=regular_user.id,
        start_time=now,
        end_time=None,
    )
    session.add(time_entry)
    session.commit()

    another_time_entry = TimeEntry(
        user_id=regular_user.id,
        start_time=now + timedelta(minutes=5),
        end_time=None,
    )
    session.add(another_time_entry)

    with pytest.raises(IntegrityError):
        session.commit()


def test_db_enforces_end_after_start_check_constraint(session, regular_user):
    now = _now()

    invalid_time_entry = TimeEntry(
        user_id=regular_user.id,
        start_time=now,
        end_time=now - timedelta(minutes=15),
    )
    session.add(invalid_time_entry)

    with pytest.raises(IntegrityError):
        session.commit()
