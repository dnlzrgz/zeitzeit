from unittest.mock import patch

from app.src.users.services import authenticate, create
from app.models import UserCreate


def test_authenticate_returns_user_with_correct_credentials(session, faker):
    email = faker.email()
    password = faker.password()
    create(session=session, user_create=UserCreate(email=email, password=password))

    user = authenticate(session=session, email=email, password=password)

    assert user is not None
    assert user.email == email


def test_authenticate_returns_none_with_wrong_password(session, faker):
    email = faker.email()
    create(
        session=session, user_create=UserCreate(email=email, password=faker.password())
    )

    result = authenticate(session=session, email=email, password="wrongpassword123")

    assert result is None


def test_authenticate_returns_none_for_nonexistent_user(session, faker):
    result = authenticate(
        session=session, email=faker.email(), password=faker.password()
    )

    assert result is None


def test_authenticate_runs_dummy_hash_for_nonexistent_user(session, faker):
    with patch("app.src.users.services.verify_password") as mock_verify:
        authenticate(session=session, email=faker.email(), password=faker.password())

    mock_verify.assert_called_once()


def test_authenticate_returns_user_even_if_inactive(session, faker):
    email = faker.email()
    password = faker.password()
    user = create(
        session=session, user_create=UserCreate(email=email, password=password)
    )
    user.is_active = False
    session.add(user)
    session.commit()

    result = authenticate(session=session, email=email, password=password)

    assert result is not None
