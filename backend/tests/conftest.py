from collections.abc import Generator
from datetime import timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from starlette.testclient import TestClient

from app import security
from app.db import get_db
from app.main import app
from app.models import User, UserCreate
from app.src.users import services as user_services


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    yield engine

    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def session(engine) -> Generator[Session, None, None]:
    conn = engine.connect()
    outer_transaction = conn.begin()

    session = Session(
        bind=conn,
        join_transaction_mode="create_savepoint",
    )

    yield session

    session.close()
    outer_transaction.rollback()
    conn.close()


@pytest.fixture()
def client(session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def admin(session: Session, faker) -> User:
    return user_services.create(
        session=session,
        user_create=UserCreate(
            email=faker.unique.email(),
            password=faker.unique.password(),
            is_admin=True,
        ),
    )


@pytest.fixture()
def admin_token_headers(admin: User) -> dict[str, str]:
    token = security.create_access_token(
        subject=str(admin.id), expires_delta=timedelta(minutes=30)
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def regular_user(session: Session, faker) -> User:
    return user_services.create(
        session=session,
        user_create=UserCreate(
            email=faker.unique.email(),
            password=faker.unique.password(),
            is_admin=False,
        ),
    )


@pytest.fixture()
def regular_user_token_headers(regular_user: User) -> dict[str, str]:
    token = security.create_access_token(
        subject=str(regular_user.id), expires_delta=timedelta(minutes=30)
    )

    return {"Authorization": f"Bearer {token}"}
