from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, SessionDep
from app.models import (
    ProjectCreate,
    ProjectPublic,
    ProjectsPublic,
    ProjectUpdate,
)
from app.src.projects import services

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/{project_id}", response_model=ProjectPublic)
def get_project(
    session: SessionDep,
    current_user: CurrentUser,
    project_id: UUID,
) -> Any:
    project = services.get(
        session=session, user_id=current_user.id, project_id=project_id
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return project


@router.get("/", response_model=ProjectsPublic)
def list_projects(session: SessionDep, current_user: CurrentUser) -> Any:
    projects, count = services.list_all(session=session, user_id=current_user.id)
    return {"data": projects, "count": count}


@router.post("/", response_model=ProjectPublic, status_code=201)
def create_project(
    session: SessionDep,
    current_user: CurrentUser,
    project_in: ProjectCreate,
) -> Any:
    try:
        return services.create(
            session=session,
            user_id=current_user.id,
            project_in=project_in,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with this name already exists",
        )


@router.patch("/{project_id}", response_model=ProjectPublic)
def update_project(
    session: SessionDep,
    current_user: CurrentUser,
    project_id: UUID,
    project_in: ProjectUpdate,
) -> Any:
    project = services.get(
        session=session, project_id=project_id, user_id=current_user.id
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    try:
        return services.update(
            session=session, db_project=project, project_in=project_in
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with this name already exists",
        )


@router.delete("/{project_id}", status_code=204)
def delete_project(session: SessionDep, current_user: CurrentUser, project_id: UUID):
    project = services.get(
        session=session, project_id=project_id, user_id=current_user.id
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    services.delete(session=session, db_project=project)
