import base64
import sqlite3
import time
from pathlib import Path

import pytest
import urllib3
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


def token(username: str = "student", role: str = "STUDENT") -> str:
    raw = f"{username}|{role}|{int(time.time()) + 3600}|WORKSHOP_SECRET_2026"
    return base64.b64encode(raw.encode()).decode()


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(username, role)}"}


def create_test_app(tmp_path: Path) -> FastAPI:
    return create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))


def create_test_client(tmp_path: Path, raise_server_exceptions: bool = True) -> TestClient:
    return TestClient(
        create_test_app(tmp_path),
        raise_server_exceptions=raise_server_exceptions,
    )


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_creates_task_and_summary(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage"},
        )
        tasks = client.get("/api/tasks", headers=headers())
        summary = client.get("/api/summary", headers=headers())
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    assert created.json()["status"] == "TODO"
    assert created.json()["priority"] == "MEDIUM"
    assert any(task["id"] == created.json()["id"] for task in tasks.json())
    assert summary.json()["total"] == 3


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    with create_test_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()
    assert (upload_dir / "requirements.txt").read_bytes() == b"Login must be accessible"
    assert response.json()["fileName"] == "requirements.txt"
    assert response.json()["size"] == len(b"Login must be accessible")


def test_rejects_invalid_token(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_list_and_summary_keep_observed_response_shapes(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        tasks = client.get("/api/tasks", headers=headers())
        summary = client.get("/api/summary", headers=headers())

    assert tasks.status_code == 200
    assert set(tasks.json()[0]) == {
        "id",
        "title",
        "description",
        "status",
        "owner",
        "priority",
        "createdAt",
    }
    assert summary.status_code == 200
    assert summary.json() == {
        "owner": "student",
        "total": 2,
        "byStatus": {"TODO": 1, "IN_PROGRESS": 1},
        "highPriorityOpen": 1,
    }


def test_create_keeps_observed_response_shape_and_defaults(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage"},
        )

    assert response.status_code == 201
    assert set(response.json()) == {
        "id",
        "title",
        "description",
        "status",
        "owner",
        "priority",
        "createdAt",
    }
    assert response.json()["status"] == "TODO"
    assert response.json()["priority"] == "MEDIUM"


def test_list_and_summary_reject_another_owner(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        tasks = client.get("/api/tasks", params={"owner": "trainer"}, headers=headers())
        summary = client.get("/api/summary", params={"owner": "trainer"}, headers=headers())

    assert tasks.status_code == 403
    assert tasks.json() == {"detail": "Forbidden"}
    assert summary.status_code == 403
    assert summary.json() == {"detail": "Forbidden"}


def test_create_rejects_another_owner(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Foreign task", "description": "Must not be assigned", "owner": "trainer"},
        )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("method", "path", "request_options"),
    [
        ("GET", "/api/tasks", {}),
        ("POST", "/api/tasks", {"json": {}}),
        ("GET", "/api/summary", {}),
        (
            "POST",
            "/api/requirements",
            {"files": {"file": ("requirement.txt", b"sample", "text/plain")}},
        ),
        ("GET", "/api/backend-health", {}),
    ],
)
def test_every_endpoint_rejects_missing_authentication(
    tmp_path: Path,
    method: str,
    path: str,
    request_options: dict[str, object],
) -> None:
    with create_test_client(tmp_path) as client:
        response = client.request(method, path, **request_options)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_list_uses_identity_when_owner_is_empty(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.get(
            "/api/tasks",
            params={"owner": ""},
            headers=headers(),
        )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert {task["owner"] for task in response.json()} == {"student"}


def test_create_empty_object_uses_documented_defaults(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.post("/api/tasks", headers=headers(), json={})

    assert response.status_code == 201
    assert response.json()["title"] == ""
    assert response.json()["description"] == ""
    assert response.json()["status"] == "TODO"
    assert response.json()["priority"] == "MEDIUM"
    assert response.json()["owner"] == "student"


def test_summary_for_user_without_tasks_is_empty(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.get("/api/summary", headers=headers("new-user"))

    assert response.status_code == 200
    assert response.json() == {
        "owner": "new-user",
        "total": 0,
        "byStatus": {},
        "highPriorityOpen": 0,
    }


def test_create_stores_quotes_as_literal_task_text(tmp_path: Path) -> None:
    with create_test_client(tmp_path, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Owner's notes", "description": "Keep punctuation"},
        )

    assert response.status_code == 201
    assert response.json()["title"] == "Owner's notes"


def test_owner_filter_treats_quotes_as_literal_value(tmp_path: Path) -> None:
    owner = "missing'owner"
    with create_test_client(tmp_path, raise_server_exceptions=False) as client:
        response = client.get("/api/tasks", params={"owner": owner}, headers=headers(owner))

    assert response.status_code == 200
    assert response.json() == []


def test_upload_rejects_path_components(tmp_path: Path) -> None:
    with create_test_client(tmp_path, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("../escape.txt", b"test content", "text/plain")},
        )

    assert response.status_code == 400
    assert not (tmp_path / "escape.txt").exists()


def test_upload_rejects_disallowed_extension(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("payload.exe", b"test content", "application/octet-stream")},
        )

    assert response.status_code == 400


def test_upload_rejects_filename_without_extension(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements", b"test content", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported file type"}


def test_upload_without_file_returns_validation_error(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.post("/api/requirements", headers=headers())

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "file"]
    assert response.json()["detail"][0]["type"] == "missing"


def test_upload_enforces_five_mib_limit(tmp_path: Path) -> None:
    oversized_content = b"x" * (5 * 1024 * 1024 + 1)
    with create_test_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("large.txt", oversized_content, "text/plain")},
        )

    assert response.status_code == 413


def test_upload_accepts_five_mib_file(tmp_path: Path) -> None:
    accepted_content = b"x" * (5 * 1024 * 1024)
    with create_test_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("large.txt", accepted_content, "text/plain")},
        )

    assert response.status_code == 201
    assert response.json()["size"] == 5 * 1024 * 1024


def test_create_rejects_invalid_task_field_types(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": [], "description": "Invalid title"},
        )

    assert response.status_code == 422


def test_invalid_token_error_does_not_expose_parser_details(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_backend_health_keeps_success_response_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class HealthResponse:
        status = 200
        data = b'{"status":"UP"}'

    class HealthManager:
        def request(self, method: str, url: str, timeout: float) -> HealthResponse:
            assert method == "GET"
            assert url == "http://localhost:8080/q/health"
            assert timeout == 3.0
            return HealthResponse()

    monkeypatch.setattr("urllib3.PoolManager", lambda: HealthManager())
    with create_test_client(tmp_path) as client:
        response = client.get("/api/backend-health", headers=headers())

    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 200,
        "body": '{"status":"UP"}',
    }


def test_backend_health_error_is_generic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingHealthManager:
        def request(self, method: str, url: str, timeout: float) -> None:
            assert method == "GET"
            assert url == "http://localhost:8080/q/health"
            assert timeout == 3.0
            raise urllib3.exceptions.HTTPError("internal backend connection detail")

    monkeypatch.setattr("urllib3.PoolManager", lambda: FailingHealthManager())
    with create_test_client(tmp_path) as client:
        response = client.get("/api/backend-health", headers=headers())

    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 0,
        "body": "Backend health check failed",
    }
    assert "internal backend connection detail" not in response.text


def test_backend_health_preserves_downstream_error_status_as_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnavailableHealthResponse:
        status = 503
        data = b"Service unavailable"

    class UnavailableHealthManager:
        def request(self, method: str, url: str, timeout: float) -> UnavailableHealthResponse:
            assert method == "GET"
            assert url == "http://localhost:8080/q/health"
            assert timeout == 3.0
            return UnavailableHealthResponse()

    monkeypatch.setattr("urllib3.PoolManager", lambda: UnavailableHealthManager())
    with create_test_client(tmp_path) as client:
        response = client.get("/api/backend-health", headers=headers())

    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 503,
        "body": "Service unavailable",
    }


@pytest.mark.parametrize(
    ("method", "path", "repository_method", "request_options"),
    [
        ("GET", "/api/tasks", "list_for_owner", {"headers": headers()}),
        ("POST", "/api/tasks", "create", {"headers": headers(), "json": {}}),
        ("GET", "/api/summary", "summary_for_owner", {"headers": headers()}),
    ],
)
def test_task_endpoints_return_generic_database_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: str,
    repository_method: str,
    request_options: dict[str, object],
) -> None:
    app = create_test_app(tmp_path)

    def fail_database_operation(*_args: object, **_kwargs: object) -> None:
        assert _args
        assert not _kwargs
        raise sqlite3.OperationalError("private database connection detail")

    monkeypatch.setattr(app.state.repository, repository_method, fail_database_operation)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.request(method, path, **request_options)

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert "private database connection detail" not in response.text


def test_upload_storage_error_is_generic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_file_write(_path: Path, _content: bytes) -> int:
        assert _path.name == "requirement.txt"
        assert _content == b"sample"
        raise OSError("private filesystem detail")

    monkeypatch.setattr(Path, "write_bytes", fail_file_write)
    with create_test_client(tmp_path, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirement.txt", b"sample", "text/plain")},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Unable to store uploaded file"}
    assert "private filesystem detail" not in response.text


def test_backend_health_unhandled_error_returns_generic_500(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class CrashingHealthManager:
        def request(self, method: str, url: str, timeout: float) -> None:
                assert method == "GET"
                assert url == "http://localhost:8080/q/health"
                assert timeout == 3.0
                raise RuntimeError("private backend implementation detail")

    monkeypatch.setattr("urllib3.PoolManager", lambda: CrashingHealthManager())
    with create_test_client(tmp_path, raise_server_exceptions=False) as client:
        response = client.get("/api/backend-health", headers=headers())

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert "private backend implementation detail" not in response.text
