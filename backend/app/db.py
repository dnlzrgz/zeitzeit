from typing import Generator

from sqlalchemy import event
from sqlmodel import Session, create_engine, select

from app.models import User, UserCreate
from app.settings import settings


def get_engine(uri: str = settings.SQLALCHEMY_DATABASE_URI):
    if settings.DB_BACKEND == "sqlite":
        engine = create_engine(uri)
        opts = settings.SQLITE_OPTIONS

        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            for pragma in opts.as_pragmas():
                cursor.execute(pragma)

            cursor.close()

        return engine

    return create_engine(uri)


def init_db(session: Session) -> None:
    # Tables should be created using Alembic.
    from app.src.users import services as user_services

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_admin=True,
        )

        user_services.create(session=session, user_create=user_in)


engine = get_engine()


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
