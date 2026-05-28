from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.models import TimeEntryCreate, TimeEntryUpdate
from tests.utils import _now


def test_create_with_no_end_time_is_valid():
    time_entry = TimeEntryCreate(start_time=_now())
    assert time_entry.end_time is None


def test_create_end_time_equal_to_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryCreate(start_time=now, end_time=now)


def test_create_end_time_before_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryCreate(start_time=now + timedelta(minutes=30), end_time=now)


def test_update_end_time_after_start_is_valid():
    now = _now()
    TimeEntryUpdate(start_time=now, end_time=now + timedelta(minutes=30))


def test_update_end_time_equal_to_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryUpdate(start_time=now, end_time=now)


def test_update_end_time_before_start_raises_error():
    now = _now()
    with pytest.raises(ValidationError):
        TimeEntryCreate(start_time=now + timedelta(minutes=30), end_time=now)
