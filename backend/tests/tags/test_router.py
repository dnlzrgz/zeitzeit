from fastapi import status

from app.main import app
from tests.utils import _create_tag


def test_get_tag_by_id_requires_authentication(session, client, regular_user) -> None:
    tag = _create_tag(session, regular_user.id)
    resp = client.get(app.url_path_for("get_tag", tag_id=tag.id))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_tag_by_id_returns_tag_successfully(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    tag = _create_tag(session, regular_user.id)
    resp = client.get(
        app.url_path_for("get_tag", tag_id=tag.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["id"] == str(tag.id)
    assert body["name"] == tag.name


def test_get_tag_by_id_not_found_returns_404(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.get(
        app.url_path_for("get_tag", tag_id=faker.uuid4()),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_get_tag_by_id_from_another_user_returns_404(
    session,
    client,
    admin,
    regular_user_token_headers,
) -> None:
    admin_tag = _create_tag(session, admin.id)
    resp = client.get(
        app.url_path_for("get_tag", tag_id=admin_tag.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_create_tag_requires_authentication(client) -> None:
    resp = client.post(app.url_path_for("create_tag"), json={"name": "x"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_tag_creates_tag_successfully(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    name = faker.unique.word()
    resp = client.post(
        app.url_path_for("create_tag"),
        json={"name": name},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["name"] == name


def test_create_tag_with_duplicate_name_returns_409(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    _create_tag(session, regular_user.id, "duplicated")
    resp = client.post(
        app.url_path_for("create_tag"),
        json={"name": "duplicated"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_create_tag_same_name_allowed_for_different_users(
    session,
    client,
    regular_user,
    admin_token_headers,
) -> None:
    _create_tag(session, regular_user.id, name="shared")

    resp = client.post(
        app.url_path_for("create_tag"),
        json={"name": "shared"},
        headers=admin_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["name"] == "shared"


def test_list_tags_requires_authentication(client) -> None:
    resp = client.get(app.url_path_for("list_tags"))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_tags_returns_empty_list_when_no_tags(
    client,
    regular_user_token_headers,
) -> None:
    resp = client.get(app.url_path_for("list_tags"), headers=regular_user_token_headers)
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["data"] == []
    assert body["count"] == 0


def test_list_tags_returns_only_own_tags(
    session,
    client,
    regular_user,
    regular_user_token_headers,
    admin,
) -> None:
    for _ in range(5):
        _create_tag(session, regular_user.id)
        _create_tag(session, admin.id)

    resp = client.get(app.url_path_for("list_tags"), headers=regular_user_token_headers)
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["count"] == 5


def test_update_tag_requires_authentication(session, client, regular_user) -> None:
    tag = _create_tag(session, regular_user.id)
    resp = client.patch(
        app.url_path_for("update_tag", tag_id=tag.id),
        json={"name": "y"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_tag_updates_tag_successfully(
    session,
    client,
    faker,
    regular_user,
    regular_user_token_headers,
) -> None:
    tag = _create_tag(session, regular_user.id)
    new_name = faker.unique.word()
    resp = client.patch(
        app.url_path_for("update_tag", tag_id=tag.id),
        json={"name": new_name},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["name"] == new_name


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
    assert resp.json()["name"] == "unique"


def test_update_tag_from_another_user_returns_404(
    session,
    client,
    faker,
    admin,
    regular_user_token_headers,
) -> None:
    admin_tag = _create_tag(session, admin.id)
    resp = client.patch(
        app.url_path_for("update_tag", tag_id=admin_tag.id),
        json={"name": faker.unique.word()},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_tag_requires_authentication(session, client, regular_user) -> None:
    tag = _create_tag(session, regular_user.id)
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
    tag = _create_tag(session, regular_user.id)
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
    admin_tag = _create_tag(session, admin.id)
    resp = client.delete(
        app.url_path_for("delete_tag", tag_id=admin_tag.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
