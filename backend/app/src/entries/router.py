from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import CurrentUser, SessionDep
from app.models import (
    TimeEntriesPage,
    TimeEntryCreate,
    TimeEntryPublic,
    TimeEntryUpdate,
)
from app.src.entries import services

router = APIRouter(
    prefix="/time-entries",
    tags=["time-entries"],
)


@router.get("/running", response_model=TimeEntryPublic | None)
def get_running_entry(session: SessionDep, current_user: CurrentUser) -> Any:
    return services.get_running(session=session, user_id=current_user.id)


@router.get("/{time_entry_id}", response_model=TimeEntryPublic)
def get_time_entry(
    session: SessionDep,
    current_user: CurrentUser,
    time_entry_id: UUID,
):
    time_entry = services.get(
        session=session, user_id=current_user.id, time_entry_id=time_entry_id
    )
    if not time_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Time entry not found"
        )

    return time_entry


@router.get("/", response_model=TimeEntriesPage)
def list_time_entries(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: UUID | None = None,
) -> Any:
    items, next_cursor, has_more = services.list_paginated(
        session=session,
        user_id=current_user.id,
        limit=limit,
        cursor=cursor,
    )

    return {
        "data": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.post("/", response_model=TimeEntryPublic, status_code=201)
def create_time_entry(
    session: SessionDep,
    current_user: CurrentUser,
    time_entry_in: TimeEntryCreate,
) -> Any:
    return services.create(
        session=session,
        user_id=current_user.id,
        time_entry_in=time_entry_in,
    )


@router.patch("/{time_entry_id}", response_model=TimeEntryPublic)
def update_time_entry(
    session: SessionDep,
    current_user: CurrentUser,
    time_entry_id: UUID,
    time_entry_in: TimeEntryUpdate,
) -> Any:
    time_entry = services.get(
        session=session, time_entry_id=time_entry_id, user_id=current_user.id
    )
    if not time_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found",
        )
    return services.update(
        session=session,
        db_time_entry=time_entry,
        time_entry_in=time_entry_in,
    )


@router.post("/{time_entry_id}/stop", response_model=TimeEntryPublic)
def stop_time_entry(
    session: SessionDep, current_user: CurrentUser, time_entry_id: UUID
) -> Any:
    time_entry = services.get(
        session=session, time_entry_id=time_entry_id, user_id=current_user.id
    )
    if not time_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Time entry not found"
        )

    if time_entry.end_time is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Time entry is already stopped"
        )

    return services.stop(session=session, db_time_entry=time_entry)


@router.delete("/{time_entry_id}", status_code=204)
def delete_time_entry(
    session: SessionDep, current_user: CurrentUser, time_entry_id: UUID
) -> None:
    time_entry = services.get(
        session=session, time_entry_id=time_entry_id, user_id=current_user.id
    )
    if not time_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found",
        )
    services.delete(session=session, db_time_entry=time_entry)
