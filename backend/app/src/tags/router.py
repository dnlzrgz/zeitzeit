from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, SessionDep
from app.models import TagCreate, TagPublic, TagsPublic, TagUpdate
from app.src.tags import services

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/{tag_id}", response_model=TagPublic)
def get_tag(session: SessionDep, current_user: CurrentUser, tag_id: UUID) -> Any:
    tag = services.get(session=session, user_id=current_user.id, tag_id=tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    return tag


@router.get("/", response_model=TagsPublic)
def list_tags(session: SessionDep, current_user: CurrentUser) -> Any:
    tags, count = services.list_all(session=session, user_id=current_user.id)
    return {"data": tags, "count": count}


@router.post("/", response_model=TagPublic, status_code=201)
def create_tag(
    session: SessionDep,
    current_user: CurrentUser,
    tag_in: TagCreate,
) -> Any:
    try:
        return services.create(session=session, user_id=current_user.id, tag_in=tag_in)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tag with this name already exists",
        )


@router.patch("/{tag_id}", response_model=TagPublic)
def update_tag(
    session: SessionDep,
    current_user: CurrentUser,
    tag_id: UUID,
    tag_in: TagUpdate,
) -> Any:
    tag = services.get(session=session, tag_id=tag_id, user_id=current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    try:
        return services.update(session=session, db_tag=tag, tag_in=tag_in)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tag with this name already exists",
        )


@router.delete("/{tag_id}", status_code=204)
def delete_tag(session: SessionDep, current_user: CurrentUser, tag_id: UUID):
    tag = services.get(session=session, tag_id=tag_id, user_id=current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    services.delete(session=session, db_tag=tag)
