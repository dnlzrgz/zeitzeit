from fastapi import status

from app.main import app
from app.models import UserCreate
from app.src.users import services as user_services


def test_login_with_valid_credentials_returns_200_and_token(
    client, session, faker
) -> None:
    email = faker.unique.email()
    password = faker.unique.password()
    user_services.create(
        session=session,
        user_create=UserCreate(email=email, password=password),
    )

    resp = client.post(
        app.url_path_for("login_access_token"),
        data={"username": email, "password": password},
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_with_wrong_password_returns_400(client, session, faker) -> None:
    email = faker.unique.email()
    password = faker.unique.password()
    user_services.create(
        session=session,
        user_create=UserCreate(email=email, password=password),
    )

    resp = client.post(
        app.url_path_for("login_access_token"),
        data={"username": email, "password": "wrongpassword123"},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_login_with_inactive_user_returns_400(client, session, faker) -> None:
    email = faker.unique.email()
    password = faker.unique.password()
    user = user_services.create(
        session=session,
        user_create=UserCreate(email=email, password=password),
    )
    user.is_active = False
    session.add(user)
    session.commit()

    resp = client.post(
        app.url_path_for("login_access_token"),
        data={"username": email, "password": password},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
