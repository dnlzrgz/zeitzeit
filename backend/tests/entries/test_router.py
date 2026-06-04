from datetime import timedelta

from fastapi import status

from app.main import app
from app.src.entries import services as entry_services
from tests.utils import _create_project, _create_tag, _create_time_entry, _now


def test_get_time_entry_by_id_requires_authentication(
    session,
    client,
    regular_user,
) -> None:
    entry = _create_time_entry(session, regular_user.id)
    resp = client.get(app.url_path_for("get_time_entry", time_entry_id=entry.id))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_time_entry_by_id_returns_entry_successfully(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    entry = _create_time_entry(session, regular_user.id)
    resp = client.get(
        app.url_path_for("get_time_entry", time_entry_id=entry.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["id"] == str(entry.id)
    assert body["description"] == entry.description


def test_get_time_entry_by_id_not_found_returns_404(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.get(
        app.url_path_for("get_time_entry", time_entry_id=faker.uuid4()),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_get_time_entry_by_id_from_another_user_returns_404(
    session,
    client,
    admin,
    regular_user_token_headers,
) -> None:
    admin_entry = _create_time_entry(session, admin.id)
    resp = client.get(
        app.url_path_for("get_time_entry", time_entry_id=admin_entry.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_get_running_entry_requires_authentication(client) -> None:
    resp = client.get(app.url_path_for("get_running_entry"))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_running_entry_returns_none_when_no_running_entry(
    client,
    regular_user_token_headers,
) -> None:
    resp = client.get(
        app.url_path_for("get_running_entry"),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() is None


def test_get_running_entry_returns_entry_without_end_time(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    running = _create_time_entry(session, regular_user.id, end_time=None)
    resp = client.get(
        app.url_path_for("get_running_entry"),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["id"] == str(running.id)
    assert resp.json()["end_time"] is None


def test_get_running_entry_returns_only_own_entry(
    session,
    client,
    admin,
    regular_user_token_headers,
) -> None:
    _create_time_entry(session, admin.id, end_time=None)
    resp = client.get(
        app.url_path_for("get_running_entry"),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() is None


def test_stop_time_entry_requires_authentication(
    session,
    client,
    regular_user,
) -> None:
    entry = _create_time_entry(session, regular_user.id, end_time=None)
    resp = client.post(app.url_path_for("stop_time_entry", time_entry_id=entry.id))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_stop_time_entry_successfully(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    entry = _create_time_entry(session, regular_user.id, end_time=None)
    resp = client.post(
        app.url_path_for("stop_time_entry", time_entry_id=entry.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["end_time"] is not None


def test_stop_time_entry_already_stopped_returns_409(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    now = _now()
    entry = _create_time_entry(
        session,
        regular_user.id,
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    resp = client.post(
        app.url_path_for("stop_time_entry", time_entry_id=entry.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_409_CONFLICT


def test_stop_time_entry_not_found_returns_404(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.post(
        app.url_path_for("stop_time_entry", time_entry_id=faker.uuid4()),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_stop_time_entry_from_another_user_returns_404(
    session,
    client,
    admin,
    regular_user_token_headers,
) -> None:
    admin_entry = _create_time_entry(session, admin.id, end_time=None)
    resp = client.post(
        app.url_path_for("stop_time_entry", time_entry_id=admin_entry.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_create_time_entry_requires_authentication(client) -> None:
    now = _now()
    resp = client.post(
        app.url_path_for("create_time_entry"),
        json={
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(hours=1)).isoformat(),
        },
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_time_entry_successfully(
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    now = _now()
    resp = client.post(
        app.url_path_for("create_time_entry"),
        json={
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(hours=2)).isoformat(),
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED

    body = resp.json()
    assert body["user_id"] == str(regular_user.id)
    assert body["project_id"] is None
    assert body["tags"] == []


def test_create_time_entry_without_end_time_is_valid(
    client,
    regular_user_token_headers,
) -> None:
    resp = client.post(
        app.url_path_for("create_time_entry"),
        json={"start_time": _now().isoformat()},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["end_time"] is None


def test_create_time_entry_with_end_before_start_returns_422(
    client,
    regular_user_token_headers,
) -> None:
    now = _now()
    resp = client.post(
        app.url_path_for("create_time_entry"),
        json={
            "start_time": now.isoformat(),
            "end_time": (now - timedelta(hours=1)).isoformat(),
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_time_entry_with_end_equal_to_start_returns_422(
    client,
    regular_user_token_headers,
) -> None:
    now = _now()
    resp = client.post(
        app.url_path_for("create_time_entry"),
        json={
            "start_time": now.isoformat(),
            "end_time": now.isoformat(),
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_time_entry_with_project(
    session,
    client,
    faker,
    regular_user,
    regular_user_token_headers,
) -> None:
    project = _create_project(session, regular_user.id, name=faker.unique.word())
    now = _now()

    resp = client.post(
        app.url_path_for("create_time_entry"),
        json={
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(hours=1)).isoformat(),
            "project_id": str(project.id),
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["project_id"] == str(project.id)


def test_create_time_entry_with_tags(
    session,
    client,
    faker,
    regular_user,
    regular_user_token_headers,
) -> None:
    tag_a = _create_tag(session, regular_user.id, faker.unique.word())
    tag_b = _create_tag(session, regular_user.id, faker.unique.word())
    now = _now()

    resp = client.post(
        app.url_path_for("create_time_entry"),
        json={
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(hours=1)).isoformat(),
            "tag_ids": [str(tag_a.id), str(tag_b.id)],
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED

    returned_tag_ids = {t["id"] for t in resp.json()["tags"]}
    assert returned_tag_ids == {str(tag_a.id), str(tag_b.id)}


def test_list_time_entries_requires_authentication(client) -> None:
    resp = client.get(app.url_path_for("list_time_entries"))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_time_entries_returns_empty_list_when_no_entries(
    client,
    regular_user_token_headers,
) -> None:
    resp = client.get(
        app.url_path_for("list_time_entries"),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert body["has_more"] is False
    assert body["next_cursor"] is None


def test_list_time_entries_returns_only_own_entries(
    session,
    client,
    regular_user,
    regular_user_token_headers,
    admin,
) -> None:
    for _ in range(5):
        _create_time_entry(session, regular_user.id)
        _create_time_entry(session, admin.id)

    resp = client.get(
        app.url_path_for("list_time_entries"),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()

    assert len(body["data"]) == 5
    assert body["has_more"] is False
    assert body["next_cursor"] is None


def test_list_time_entries_first_page(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    for _ in range(5):
        _create_time_entry(session, regular_user.id)

    resp = client.get(
        app.url_path_for("list_time_entries"),
        params={"limit": 2},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    body = resp.json()
    assert len(body["data"]) == 2
    assert body["has_more"] is True
    assert body["next_cursor"] is not None


def test_list_time_entries_pages_do_not_overlap(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    for _ in range(10):
        _create_time_entry(session, regular_user.id)

    seen = set()
    cursor = None
    while True:
        params = {"limit": 2}
        if cursor:
            params["cursor"] = cursor

        resp = client.get(
            app.url_path_for("list_time_entries"),
            params=params,
            headers=regular_user_token_headers,
        )
        assert resp.status_code == status.HTTP_200_OK

        body = resp.json()
        page_ids = {item["id"] for item in body["data"]}

        assert seen.isdisjoint(page_ids)
        seen.update(page_ids)

        cursor = body["next_cursor"]
        if cursor is None:
            break

    assert len(seen) == 10


def test_update_time_entry_requires_authentication(
    session,
    client,
    regular_user,
) -> None:
    entry = _create_time_entry(session, regular_user.id)

    resp = client.patch(
        app.url_path_for("update_time_entry", time_entry_id=entry.id),
        json={"description": "new description"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_time_entry_description_successfully(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    entry = _create_time_entry(session, regular_user.id, description="x")

    resp = client.patch(
        app.url_path_for("update_time_entry", time_entry_id=entry.id),
        json={"description": "y"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["description"] == "y"


def test_update_time_entry_times_successfully(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    entry = _create_time_entry(session, regular_user.id)
    now = _now()

    resp = client.patch(
        app.url_path_for("update_time_entry", time_entry_id=entry.id),
        json={
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(hours=3)).isoformat(),
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK


def test_update_time_entry_with_end_before_start_returns_422(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    entry = _create_time_entry(session, regular_user.id)
    now = _now()

    resp = client.patch(
        app.url_path_for("update_time_entry", time_entry_id=entry.id),
        json={
            "start_time": now.isoformat(),
            "end_time": (now - timedelta(hours=1)).isoformat(),
        },
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_time_entry_assign_project(
    session,
    client,
    faker,
    regular_user,
    regular_user_token_headers,
) -> None:
    entry = _create_time_entry(session, regular_user.id)
    project = _create_project(session, regular_user.id, name=faker.unique.word())

    resp = client.patch(
        app.url_path_for("update_time_entry", time_entry_id=entry.id),
        json={"project_id": str(project.id)},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["project_id"] == str(project.id)


def test_update_time_entry_from_another_user_returns_404(
    session,
    client,
    admin,
    regular_user_token_headers,
) -> None:
    admin_entry = _create_time_entry(session, admin.id)

    resp = client.patch(
        app.url_path_for("update_time_entry", time_entry_id=admin_entry.id),
        json={"description": "hijacked"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_update_time_entry_not_found_returns_404(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.patch(
        app.url_path_for("update_time_entry", time_entry_id=faker.uuid4()),
        json={"description": "ghost"},
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_time_entry_requires_authentication(
    session,
    client,
    regular_user,
) -> None:
    entry = _create_time_entry(session, regular_user.id)

    resp = client.delete(
        app.url_path_for("delete_time_entry", time_entry_id=entry.id),
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_time_entry_successfully(
    session,
    client,
    regular_user,
    regular_user_token_headers,
) -> None:
    entry = _create_time_entry(session, regular_user.id)

    resp = client.delete(
        app.url_path_for("delete_time_entry", time_entry_id=entry.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    gone = entry_services.get(
        session=session, time_entry_id=entry.id, user_id=regular_user.id
    )
    assert gone is None


def test_delete_time_entry_not_found_returns_404(
    client,
    faker,
    regular_user_token_headers,
) -> None:
    resp = client.delete(
        app.url_path_for("delete_time_entry", time_entry_id=faker.uuid4()),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_time_entry_from_another_user_returns_404(
    session,
    client,
    admin,
    regular_user_token_headers,
) -> None:
    admin_entry = _create_time_entry(session, admin.id)

    resp = client.delete(
        app.url_path_for("delete_time_entry", time_entry_id=admin_entry.id),
        headers=regular_user_token_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
