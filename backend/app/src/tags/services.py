from uuid import UUID

from sqlmodel import Session, func, select

from app.models import Tag, TagCreate, TagUpdate


def get(*, session: Session, tag_id: UUID, user_id: UUID) -> Tag | None:
    return session.exec(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    ).first()


def list_all(*, session: Session, user_id: UUID) -> tuple[list[Tag], int]:
    tags = session.exec(select(Tag).where(Tag.user_id == user_id)).all()
    total = session.exec(select(func.count()).where(Tag.user_id == user_id)).one()
    return list(tags), int(total)


def create(*, session: Session, user_id: UUID, tag_in: TagCreate) -> Tag:
    tag = Tag.model_validate(tag_in, update={"user_id": user_id})
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


def update(*, session: Session, db_tag: Tag, tag_in: TagUpdate) -> Tag:
    tag_data = tag_in.model_dump(exclude_unset=True)
    db_tag.sqlmodel_update(tag_data)
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag


def delete(*, session: Session, db_tag: Tag) -> None:
    session.delete(db_tag)
    session.commit()
