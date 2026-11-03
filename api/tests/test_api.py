import base64
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def token(username: str = "student", role: str = "STUDENT") -> str:
    raw = f"{username}|{role}|{int(time.time()) + 3600}|WORKSHOP_SECRET_2026"
    return base64.b64encode(raw.encode()).decode()


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(username, role)}"}


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_creates_task_and_summary(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage", "status": "TODO", "priority": "HIGH"},
        )
        summary = client.get("/api/summary", headers=headers())
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    assert summary.json()["total"] == 3


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()


def test_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_cors_denies_origins_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("API_CORS_ALLOWED_ORIGINS", raising=False)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.options(
            "/api/tasks",
            headers={
                "Origin": "https://unlisted.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            },
        )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_only_configured_origins_and_contract_headers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "API_CORS_ALLOWED_ORIGINS",
        "http://localhost:4200, https://admin.example",
    )
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        allowed = client.options(
            "/api/tasks",
            headers={
                "Origin": "http://localhost:4200",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            },
        )
        denied = client.options(
            "/api/tasks",
            headers={
                "Origin": "https://unlisted.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            },
        )
        disallowed_method = client.options(
            "/api/tasks",
            headers={
                "Origin": "https://frontend.example",
                "Access-Control-Request-Method": "DELETE",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        allowed_request = client.get(
            "/api/tasks",
            headers={**headers(), "Origin": "http://localhost:4200"},
        )
        unlisted_request = client.get(
            "/api/tasks",
            headers={**headers(), "Origin": "https://unlisted.example"},
        )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:4200"
    assert allowed.headers["access-control-allow-methods"] == "GET, POST"
    assert "access-control-allow-credentials" not in allowed.headers
    allowed_headers = {
        header.strip().lower()
        for header in allowed.headers["access-control-allow-headers"].split(",")
    }
    assert {"authorization", "content-type"} <= allowed_headers
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers
    assert disallowed_method.status_code == 400
    assert allowed_request.status_code == 200
    assert allowed_request.headers["access-control-allow-origin"] == "http://localhost:4200"
    assert unlisted_request.status_code == 200
    assert "access-control-allow-origin" not in unlisted_request.headers


def test_cors_rejects_unrestricted_wildcard_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_CORS_ALLOWED_ORIGINS", "*")

    with pytest.raises(ValueError, match="API_CORS_ALLOWED_ORIGINS"):
        create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
