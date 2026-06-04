from fastapi import status

from app.main import app


def test_signup_creates_user_successfully(client, faker) -> None:
    email = faker.unique.email()
    resp = client.post(
        app.url_path_for("register_user"),
        json={
            "email": email,
            "password": "ValidPassword1!",
            "full_name": "Test User",
        },
    )
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["email"] == email
    assert body["full_name"] == "Test User"
    assert body["is_admin"] is False
    assert "hashed_password" not in body


def test_signup_with_duplicate_email_returns_409(
    client,
    regular_user,
    faker,
) -> None:
    resp = client.post(
        app.url_path_for("register_user"),
        json={
            "email": regular_user.email,
            "password": faker.password(),
        },
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_signup_with_short_password_returns_422(client, faker) -> None:
    resp = client.post(
        app.url_path_for("register_user"),
        json={
            "email": faker.unique.email(),
            "password": "short",
        },
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_me_requires_authentication(client) -> None:
    resp = client.get(app.url_path_for("get_me"))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_returns_current_user(
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    resp = client.get(
        app.url_path_for("get_me"),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["id"] == str(regular_user.id)
    assert body["email"] == regular_user.email
    assert "hashed_password" not in body


def test_update_me_requires_authentication(client) -> None:
    resp = client.patch(
        app.url_path_for("update_me"),
        json={"full_name": "New Name"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_me_full_name_successfully(
    client,
    regular_user_token_headers,
) -> None:
    resp = client.patch(
        app.url_path_for("update_me"),
        json={"full_name": "New Name"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["full_name"] == "New Name"


def test_update_me_email_successfully(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    new_email = faker.unique.email()
    resp = client.patch(
        app.url_path_for("update_me"),
        json={"email": new_email},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["email"] == new_email


def test_update_me_with_duplicate_email_returns_409(
    client,
    admin,
    regular_user_token_headers,
) -> None:
    resp = client.patch(
        app.url_path_for("update_me"),
        json={"email": admin.email},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_update_me_cannot_elevate_to_admin(
    client,
    regular_user_token_headers,
) -> None:
    resp = client.patch(
        app.url_path_for("update_me"),
        json={"is_admin": True},
        headers=regular_user_token_headers,
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["is_admin"] is False


def test_update_password_requires_authentication(client, faker) -> None:
    resp = client.patch(
        app.url_path_for("update_password"),
        json={
            "current_password": faker.password(),
            "new_password": faker.password(),
        },
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_password_successfully(
    client,
    regular_password,
    regular_user_token_headers,
    faker,
) -> None:
    resp = client.patch(
        app.url_path_for("update_password"),
        json={
            "current_password": regular_password,
            "new_password": faker.password(),
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_204_NO_CONTENT


def test_update_password_with_wrong_current_password_returns_400(
    client,
    regular_user_token_headers,
    faker,
) -> None:
    resp = client.patch(
        app.url_path_for("update_password"),
        json={
            "current_password": faker.password(),
            "new_password": faker.password(),
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_update_password_with_same_password_returns_400(
    client,
    regular_password,
    regular_user_token_headers,
) -> None:
    resp = client.patch(
        app.url_path_for("update_password"),
        json={
            "current_password": regular_password,
            "new_password": regular_password,
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
