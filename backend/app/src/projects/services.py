from uuid import UUID

from sqlmodel import Session, func, select

from app.models import Project, ProjectCreate, ProjectUpdate


def get(*, session: Session, project_id: UUID, user_id: UUID) -> Project | None:
    return session.exec(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    ).first()


def list_all(*, session: Session, user_id: UUID) -> tuple[list[Project], int]:
    projects = session.exec(select(Project).where(Project.user_id == user_id)).all()
    total = session.exec(select(func.count()).where(Project.user_id == user_id)).one()
    return list(projects), int(total)


def create(*, session: Session, user_id: UUID, project_in: ProjectCreate) -> Project:
    project = Project.model_validate(project_in, update={"user_id": user_id})
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def update(
    *, session: Session, db_project: Project, project_in: ProjectUpdate
) -> Project:
    project_data = project_in.model_dump(exclude_unset=True)
    db_project.sqlmodel_update(project_data)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project


def delete(*, session: Session, db_project: Project) -> None:
    session.delete(db_project)
    session.commit()
