from fastapi import status

from app.main import app
from tests.utils import _create_project


def test_create_project_requires_authentication(client) -> None:
    resp = client.post(
        app.url_path_for("create_project"),
        json={"name": "x"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_project_successfully(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.post(
        app.url_path_for("create_project"),
        json={"name": faker.unique.word(), "color": faker.hex_color()},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED


def test_create_project_with_duplicate_name_returns_409(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    _create_project(
        session,
        regular_user.id,
        name="duplicate",
    )

    resp = client.post(
        app.url_path_for("create_project"),
        json={"name": "duplicate", "color": "#ff0000"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_create_project_same_name_allowed_for_different_users(
    session,
    client,
    regular_user,
    admin_token_headers,
) -> None:
    _create_project(session, regular_user.id, name="shared")

    resp = client.post(
        app.url_path_for("create_project"),
        json={"name": "shared", "color": "#ff0000"},
        headers=admin_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED


def test_create_project_normalizes_color_to_hex(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.post(
        app.url_path_for("create_project"),
        json={"name": faker.unique.word(), "color": "red"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["color"] == "#FF0000"


def test_list_projects_requires_authentication(client) -> None:
    resp = client.get(app.url_path_for("list_projects"))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_projects_returns_empty_list_when_no_projects(
    client,
    regular_user_token_headers,
) -> None:
    resp = client.get(
        app.url_path_for("list_projects"),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["data"] == []
    assert body["count"] == 0


def test_list_projects_returns_only_own_projects(
    session,
    client,
    regular_user,
    regular_user_token_headers,
    admin,
) -> None:
    for _ in range(5):
        _create_project(session, regular_user.id)
        _create_project(session, admin.id)

    resp = client.get(
        app.url_path_for("list_projects"),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["count"] == 5


def test_update_project_requires_authentication(
    session,
    client,
    regular_user,
) -> None:
    project = _create_project(session, regular_user.id)
    resp = client.patch(
        app.url_path_for("update_project", project_id=project.id),
        json={"name": "y"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_project_name_successfully(
    session,
    client,
    faker,
    regular_user,
    regular_user_token_headers,
) -> None:
    project = _create_project(session, regular_user.id)
    resp = client.patch(
        app.url_path_for("update_project", project_id=project.id),
        json={"name": faker.unique.word()},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK


def test_update_project_color_successfully(
    session,
    client,
    faker,
    regular_user,
    regular_user_token_headers,
) -> None:
    project = _create_project(session, regular_user.id)
    resp = client.patch(
        app.url_path_for("update_project", project_id=project.id),
        json={"color": faker.unique.hex_color()},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK


def test_update_project_with_same_name_is_successful(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    project = _create_project(session, regular_user.id, name="unique")
    resp = client.patch(
        app.url_path_for("update_project", project_id=project.id),
        json={"name": "unique"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK


def test_update_project_with_duplicate_name_returns_409(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    _create_project(session, regular_user.id, name="duplicated")
    project = _create_project(session, regular_user.id)
    resp = client.patch(
        app.url_path_for("update_project", project_id=project.id),
        json={"name": "duplicated"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_update_project_from_another_user_returns_404(
    session,
    client,
    faker,
    admin,
    regular_user_token_headers,
) -> None:
    admin_project = _create_project(session, admin.id)
    resp = client.patch(
        app.url_path_for("update_project", project_id=admin_project.id),
        json={"name": faker.unique.word()},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_update_project_not_found_returns_404(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.patch(
        app.url_path_for("update_project", project_id=faker.uuid4()),
        json={"name": "ghost"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_project_requires_authentication(
    session,
    client,
    regular_user,
) -> None:
    project = _create_project(session, regular_user.id)
    resp = client.delete(
        app.url_path_for("delete_project", project_id=project.id),
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_project_successfully(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    project = _create_project(session, regular_user.id)
    resp = client.delete(
        app.url_path_for("delete_project", project_id=project.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_204_NO_CONTENT


def test_delete_project_not_found_returns_404(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.delete(
        app.url_path_for("delete_project", project_id=faker.uuid4()),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_project_from_another_user_returns_404(
    session,
    client,
    admin,
    regular_user_token_headers,
) -> None:
    admin_project = _create_project(session, admin.id)
    resp = client.delete(
        app.url_path_for("delete_project", project_id=admin_project.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
