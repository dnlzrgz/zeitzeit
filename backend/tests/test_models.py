from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.models import TimeEntryCreate, TimeEntryUpdate


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dt(offset_mins: int = 0) -> datetime:
    return _now() + timedelta(minutes=offset_mins)


def test_create_with_no_end_time_is_valid():
    time_entry = TimeEntryCreate(start_time=_now())
    assert time_entry.end_time is None


def test_create_end_time_equal_to_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryCreate(start_time=now, end_time=now)


def test_create_end_time_before_start_raises_error():
    with pytest.raises(ValidationError):
        TimeEntryCreate(start_time=_dt(20), end_time=_now())


def test_update_end_time_after_start_is_valid():
    TimeEntryUpdate(start_time=_now(), end_time=_dt(20))


def test_update_end_time_equal_to_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryUpdate(start_time=now, end_time=now)


def test_update_end_time_before_start_raises_error():
    with pytest.raises(ValidationError):
        TimeEntryUpdate(start_time=_dt(20), end_time=_now())
