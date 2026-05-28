from uuid import UUID

from sqlmodel import Session, func, select

from app.models import Tag, TimeEntry, TimeEntryCreate, TimeEntryUpdate


def get(*, session: Session, time_entry_id: UUID, user_id: UUID) -> TimeEntry | None:
    return session.exec(
        select(TimeEntry).where(
            TimeEntry.id == time_entry_id, TimeEntry.user_id == user_id
        )
    ).first()


def list_all(*, session: Session, user_id: UUID) -> tuple[list[TimeEntry], int]:
    time_entries = session.exec(
        select(TimeEntry).where(TimeEntry.user_id == user_id)
    ).all()
    total = session.exec(select(func.count()).where(TimeEntry.user_id == user_id)).one()
    return list(time_entries), int(total)


def create(
    *, session: Session, user_id: UUID, time_entry_in: TimeEntryCreate
) -> TimeEntry:
    tag_ids = time_entry_in.tag_ids

    time_entry = TimeEntry.model_validate(
        time_entry_in,
        update={"user_id": user_id},
    )

    if tag_ids:
        tags = session.exec(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
        ).all()
        time_entry.tags = list(tags)

    session.add(time_entry)
    session.commit()
    session.refresh(time_entry)
    return time_entry


def update(
    *,
    session: Session,
    db_time_entry: TimeEntry,
    time_entry_in: TimeEntryUpdate,
) -> TimeEntry:
    time_entry_data = time_entry_in.model_dump(exclude_unset=True)
    tag_ids = time_entry_data.pop("tag_ids", None)

    db_time_entry.sqlmodel_update(time_entry_data)

    if tag_ids is not None:
        tags = session.exec(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == db_time_entry.user_id)
        ).all()
        db_time_entry.tags = list(tags)

    session.add(db_time_entry)
    session.commit()
    session.refresh(db_time_entry)
    return db_time_entry


def delete(*, session: Session, db_time_entry: TimeEntry) -> None:
    session.delete(db_time_entry)
    session.commit()
