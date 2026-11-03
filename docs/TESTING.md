# Evidencia de pruebas — API

## Alcance

Se probaron los cinco endpoints documentados en [ENDPOINTS.md](./ENDPOINTS.md), incluidos los caminos felices, casos borde y todas las respuestas de error descritas. Los tests ejecutables están en [api/tests/test_api.py](../api/tests/test_api.py); las pruebas usan `TestClient`, una base SQLite temporal por test y stubs para no depender del servicio de autenticación externo.

Todos los casos de esta tabla se ejecutaron en esta sesión. `PASÓ` indica que el resultado observado coincidió con el esperado.

| endpoint | caso | tipo | resultado esperado |
|---|---|---|---|
| `GET /api/tasks` | Listar tareas iniciales (`test_lists_seeded_tasks`) | Camino feliz | `200`, lista con tareas del usuario — PASÓ |
| `GET /api/tasks` | Crear y volver a leer una tarea (`test_creates_task_and_summary`) | Camino feliz | `201`; la tarea creada aparece en la lista — PASÓ |
| `GET /api/tasks` | `owner` vacío usa la identidad (`test_list_uses_identity_when_owner_is_empty`) | Borde | `200`, solo tareas de `student` — PASÓ |
| `GET /api/tasks` | Sin autenticación (`test_every_endpoint_rejects_missing_authentication`) | Error | `401`, `{"detail":"Invalid token"}` — PASÓ |
| `GET /api/tasks` | Token inválido (`test_rejects_invalid_token`, `test_invalid_token_error_does_not_expose_parser_details`) | Error | `401`, detalle genérico — PASÓ |
| `GET /api/tasks` | Consultar otro owner (`test_list_and_summary_reject_another_owner`) | Error / autorización | `403`, `{"detail":"Forbidden"}` — PASÓ |
| `GET /api/tasks` | Error de repositorio (`test_task_endpoints_return_generic_database_errors`) | Error | `500`, `Internal Server Error` sin detalle interno — PASÓ |
| `POST /api/tasks` | Crear, persistir y leer una tarea (`test_creates_task_and_summary`) | Camino feliz | `201`; owner y valores predeterminados correctos, lectura posterior confirma persistencia — PASÓ |
| `POST /api/tasks` | Objeto JSON vacío (`test_create_empty_object_uses_documented_defaults`) | Borde | `201`, defaults `""`, `TODO`, `MEDIUM` y owner autenticado — PASÓ |
| `POST /api/tasks` | Sin autenticación (`test_every_endpoint_rejects_missing_authentication`) | Error | `401`, `{"detail":"Invalid token"}` — PASÓ |
| `POST /api/tasks` | Asignar a otro owner (`test_create_rejects_another_owner`) | Error / autorización | `403`, no se acepta el owner ajeno — PASÓ |
| `POST /api/tasks` | Tipo inválido (`test_create_rejects_invalid_task_field_types`) | Error | `422` — PASÓ |
| `POST /api/tasks` | Error al insertar (`test_task_endpoints_return_generic_database_errors`) | Error | `500`, respuesta genérica sin detalle de SQLite — PASÓ |
| `GET /api/summary` | Resumen de tareas iniciales (`test_list_and_summary_keep_observed_response_shapes`) | Camino feliz | `200`, total, conteos por estado y prioridad alta — PASÓ |
| `GET /api/summary` | Usuario sin tareas (`test_summary_for_user_without_tasks`) | Borde | `200`, total `0`, `byStatus: {}` y prioridad alta `0` — PASÓ |
| `GET /api/summary` | Sin autenticación (`test_every_endpoint_rejects_missing_authentication`) | Error | `401`, `{"detail":"Invalid token"}` — PASÓ |
| `GET /api/summary` | Consultar otro owner (`test_list_and_summary_reject_another_owner`) | Error / autorización | `403`, `{"detail":"Forbidden"}` — PASÓ |
| `GET /api/summary` | Error de repositorio (`test_task_endpoints_return_generic_database_errors`) | Error | `500`, `Internal Server Error` sin detalle interno — PASÓ |
| `POST /api/requirements` | Cargar archivo `.txt` permitido (`test_uploads_requirement`) | Camino feliz | `201`; nombre, tamaño y bytes guardados coinciden — PASÓ |
| `POST /api/requirements` | Archivo de exactamente 5 MiB (`test_upload_accepts_five_mib_file`) | Borde | `201`, tamaño `5242880` — PASÓ |
| `POST /api/requirements` | Ruta en el nombre (`test_upload_rejects_path_components`) | Error | `400`, `{"detail":"Invalid file name"}` y no se escribe fuera del directorio — PASÓ |
| `POST /api/requirements` | Extensión no permitida (`test_upload_rejects_disallowed_extension`) | Error | `400`, rechazo de tipo — PASÓ |
| `POST /api/requirements` | Nombre sin extensión (`test_upload_rejects_filename_without_extension`) | Borde / error | `400`, `{"detail":"Unsupported file type"}` — PASÓ |
| `POST /api/requirements` | Archivo mayor de 5 MiB (`test_upload_enforces_five_mib_limit`) | Error | `413`, `{"detail":"Uploaded file is too large"}` — PASÓ |
| `POST /api/requirements` | Falta el campo `file` (`test_upload_without_file_returns_validation_error`) | Error | `422`, error de validación en `body.file` — PASÓ |
| `POST /api/requirements` | Sin autenticación (`test_every_endpoint_rejects_missing_authentication`) | Error | `401`, `{"detail":"Invalid token"}` — PASÓ |
| `POST /api/requirements` | Falla la escritura (`test_upload_storage_error_is_generic`) | Error | `500`, `{"detail":"Unable to store uploaded file"}` sin detalle del sistema de archivos — PASÓ |
| `GET /api/backend-health` | Backend responde `200` (`test_backend_health_keeps_success_response_shape`) | Camino feliz | `200`, cuerpo y estado downstream preservados — PASÓ |
| `GET /api/backend-health` | Backend responde `503` (`test_backend_health_preserves_downstream_error_status_as_data`) | Borde | `200` en esta API; `status: 503` y cuerpo downstream preservados — PASÓ |
| `GET /api/backend-health` | Error downstream manejado (`test_backend_health_error_is_generic`) | Error documentado | `200`, `status: 0`, mensaje genérico — PASÓ |
| `GET /api/backend-health` | Sin autenticación (`test_every_endpoint_rejects_missing_authentication`) | Error | `401`, `{"detail":"Invalid token"}` — PASÓ |
| `GET /api/backend-health` | Excepción no manejada (`test_backend_health_unhandled_error_returns_generic_500`) | Error | `500`, `Internal Server Error` sin detalle interno — PASÓ |

## Código de las pruebas

El código completo y ejecutable, incluidos los tests de caracterización previos, es [`api/tests/test_api.py`](../api/tests/test_api.py). La siguiente es la parametrización ejecutable que verifica que las cinco rutas rechacen una solicitud sin credenciales:

```python
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
```

El resto del código añadido para los bordes y errores está en el mismo módulo; se reproduce a continuación para que esta evidencia incluya los casos incorporados en este paso:

```python
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


def test_summary_for_user_without_tasks(tmp_path: Path) -> None:
    with create_test_client(tmp_path) as client:
        response = client.get("/api/summary", headers=headers("new-user"))

    assert response.status_code == 200
    assert response.json() == {
        "owner": "new-user",
        "total": 0,
        "byStatus": {},
        "highPriorityOpen": 0,
    }


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
```

Los tests preexistentes y el helper `create_test_client` se mantienen en el archivo enlazado; los fragmentos de arriba son las pruebas añadidas en esta iteración.

## Ejecuciones y cobertura

| componente e IDs | directorio de trabajo | comando | código de salida | resultado |
|---|---|---|---:|---|
| `api`; H-API-01 a H-API-07, línea base | `api/` | `.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term` | `0` | `18 passed`; cobertura reportada de `app`: `96%`. |
| `api`; H-API-01 a H-API-07, suite ampliada | `api/` | `.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term` | `0` | `34 passed`, `71 warnings`, `2.68 s`; cobertura reportada de `app`: `98%`. |

La cobertura se midió con `pytest-cov`/coverage.py desde la configuración de `api/pyproject.toml` (`branch = true`, `source = ["app"]`). La medición final incluye `212` sentencias y `22` ramas: `2` sentencias sin cubrir y `2` ramas parciales. Con el denominador combinado de coverage.py, el resultado es `(212 - 2 + 22 - 2) / (212 + 22) = 230/234 = 98.29%`, redondeado por el reporte a `98%`. La cobertura solo de sentencias es `210/212 = 99.06%`.

- **Código de aplicación modificado:** ninguno en este paso; solo se modificó `api/tests/test_api.py`. La cobertura de `app` se informa como medición global de la API bajo prueba, no como una cobertura artificial de los propios tests.
- **Cobertura global de API (`app`):** `230/234 = 98.29%` por la métrica combinada de sentencias y ramas; superior al umbral de `85%`.
- Módulos de aplicación con líneas/ramas pendientes según el reporte: `api/app/repository.py` (línea 89) y `api/app/service.py` (línea 120). No se afirma cobertura del 100%.
- Pylance no encontró errores de sintaxis ni diagnósticos en `api/tests/test_api.py`.

## Fallos

- Ningún test falló en la ejecución final.
- La ejecución mostró warnings de deprecación de `FastAPI.on_event` en `api/app/main.py:81`, además de warnings de Starlette. No se cambió código de aplicación, pues este paso es de pruebas/documentación.

## Pendientes

- **H-API-01 y H-API-02:** los tests ejercitan el token Base64 legacy observado, no una identidad JWT verificable. La autorización por owner pasa con esa identidad de prueba, pero no demuestra protección ante una identidad falsificada. El contrato con el emisor JWT sigue pendiente.
- **H-API-04:** se prueban validación de ruta, extensión y tamaño. No se afirma que esté corregida la colisión/sobrescritura entre archivos con el mismo nombre; el hallazgo sigue pendiente.
- **H-API-05:** esta suite no reemplaza un análisis SCA. Se conserva la evidencia previa de dependencias en `PLAN.md`.

## Pruebas propuestas

Cuando se coordine JWT, agregar casos con tokens firmados distintos para comprobar firma inválida, `iss`, `aud`, expiración y aislamiento real entre dos identidades. Cuando se corrija H-API-04, agregar un test de dos usuarios que suben el mismo nombre y comprobar que el segundo no sobrescribe el primer archivo. Estas pruebas no se reportan como ejecutadas ni aprobadas.

## H-API-08 — Política CORS

| ejecución | comando | resultado |
|---|---|---|
| Línea base en `day1/prompting` | `python tools/lab.py test api` | `4 passed`; cobertura global de `app`: `91.07%`. |
| Después del cambio | `python tools/lab.py test api` | `7 passed`; cobertura global de `app`: `91.94%`, superior al umbral de `85%`. |

Las tres pruebas nuevas verifican que el preflight se deniegue si no hay orígenes configurados, que el origen local `http://localhost:4200` y otro origen explícitamente configurado reciban permiso con `GET`/`POST` y los encabezados `Authorization`/`Content-Type`, que un origen no listado y un método no permitido se rechacen en preflight, y que las respuestas reales solo incluyan `Access-Control-Allow-Origin` para un origen autorizado. También verifican que la configuración `*` falle al crear la aplicación y que no se habiliten credenciales cross-origin.

La ejecución final mostró 15 advertencias de deprecación de `FastAPI.on_event` y `anyio.abc.BlockingPortal`; no se modificaron porque son ajenas a H-API-08. No se validó un origen de despliegue real ni se ejecutó Compose o una prueba en navegador; hasta que se configure `API_CORS_ALLOWED_ORIGINS`, el acceso cross-origin queda cerrado por defecto.
