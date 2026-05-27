from fastapi import status

from app.main import app
from tests.utils import _create_tag


def test_create_tag_requires_authentication(client) -> None:
    resp = client.post("/api/v1/tags/", json={"name": "x"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_tag_creates_tag_successfully(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.post(
        "/api/v1/tags/",
        json={"name": f"{faker.unique.word()}"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED


def test_create_tag_with_duplicate_name_returns_409(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    _create_tag(session, regular_user.id, "duplicated")
    resp = client.post(
        "/api/v1/tags/",
        json={"name": "duplicated"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_list_tags_requires_authentication(client) -> None:
    resp = client.get("/api/v1/tags/")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_tags_returns_empty_list_when_no_tags(
    client,
    regular_user_token_headers,
) -> None:
    resp = client.get("/api/v1/tags/", headers=regular_user_token_headers)
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["data"] == []
    assert body["count"] == 0


def test_list_tags_returns_only_own_tags(
    session,
    client,
    faker,
    regular_user,
    regular_user_token_headers,
    admin,
) -> None:
    for _ in range(5):
        _create_tag(session, regular_user.id, faker.unique.word())

    for _ in range(5):
        _create_tag(session, admin.id, faker.unique.word())

    resp = client.get("/api/v1/tags/", headers=regular_user_token_headers)
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["count"] == 5


def test_update_tag_requires_authentication(session, client, regular_user) -> None:
    tag = _create_tag(session, regular_user.id, "x")
    resp = client.patch(
        app.url_path_for("update_tag", tag_id=tag.id),
        json={"name": "y"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_tag_creates_tag_successfully(
    session,
    client,
    faker,
    regular_user,
    regular_user_token_headers,
) -> None:
    tag = _create_tag(session, regular_user.id, "x")
    resp = client.patch(
        app.url_path_for("update_tag", tag_id=tag.id),
        json={"name": f"{faker.unique.word()}"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK


def test_update_tag_with_duplicate_name_returns_409(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    _create_tag(session, regular_user.id, "duplicated")
    tag = _create_tag(session, regular_user.id, "other")
    resp = client.patch(
        app.url_path_for("update_tag", tag_id=tag.id),
        json={"name": "duplicated"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_update_tag_with_same_name_is_successful(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    tag = _create_tag(session, regular_user.id, "unique")
    resp = client.patch(
        app.url_path_for("update_tag", tag_id=tag.id),
        json={"name": "unique"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK


def test_update_tag_from_another_user_returns_404(
    session,
    client,
    faker,
    admin,
    regular_user_token_headers,
) -> None:
    admin_tag = _create_tag(session, admin.id, "private")
    resp = client.patch(
        app.url_path_for("update_tag", tag_id=admin_tag.id),
        json={"name": f"{faker.unique.word()}"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_tag_requires_authentication(session, client, regular_user) -> None:
    tag = _create_tag(session, regular_user.id, "x")
    resp = client.delete(
        app.url_path_for("delete_tag", tag_id=tag.id),
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_tag_successfully(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    tag = _create_tag(session, regular_user.id, "nothing important")
    resp = client.delete(
        app.url_path_for("delete_tag", tag_id=tag.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_204_NO_CONTENT


def test_delete_tag_not_found_returns_404(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.delete(
        app.url_path_for("delete_tag", tag_id=faker.uuid4()),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_tag_from_another_user_returns_404(
    session,
    client,
    admin,
    regular_user_token_headers,
) -> None:
    admin_tag = _create_tag(session, admin.id, "private")
    resp = client.delete(
        app.url_path_for("delete_tag", tag_id=admin_tag.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
