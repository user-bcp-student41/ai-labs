from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from fastapi import Body, Depends, FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    BackendHealthResponse,
    CreateTaskRequest,
    Identity,
    RequirementUploadResponse,
    TaskResponse,
    TaskSummaryResponse,
)
from app.repository import TaskRepository
from app.security import legacy_identity
from app.service import TaskService, backend_health as get_backend_health, store_requirement


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    selected_db = db_path or os.getenv("WORKSHOP_DB_PATH", "./data/workshop.db")
    selected_uploads = upload_dir or os.getenv("WORKSHOP_UPLOAD_DIR", "./uploads")
    Path(selected_db).parent.mkdir(parents=True, exist_ok=True)
    Path(selected_uploads).mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(selected_db, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    repository = TaskRepository(connection)
    repository.initialize()

    app = FastAPI(title="Workshop Requirements API", version="0.1.0")
    app.state.connection = connection
    app.state.repository = repository
    app.state.upload_dir = selected_uploads
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    task_service = TaskService(repository)

    @app.get("/api/tasks")
    def list_tasks(
        owner: str | None = Query(default=None),
        identity: Identity = Depends(legacy_identity),
    ) -> list[TaskResponse]:
        return task_service.list_tasks(identity, owner)

    @app.post("/api/tasks", status_code=201)
    def create_task(
        payload: CreateTaskRequest = Body(...),
        identity: Identity = Depends(legacy_identity),
    ) -> TaskResponse:
        return task_service.create_task(identity, payload)

    @app.get("/api/summary")
    def summary(
        owner: str | None = Query(default=None),
        identity: Identity = Depends(legacy_identity),
    ) -> TaskSummaryResponse:
        return task_service.summary(identity, owner)

    @app.post("/api/requirements", status_code=201)
    async def upload_requirement(
        file: UploadFile = File(...),
        identity: Identity = Depends(legacy_identity),
    ) -> RequirementUploadResponse:
        return await store_requirement(file, identity, Path(selected_uploads))

    @app.get("/api/backend-health")
    def backend_health(
        identity: Identity = Depends(legacy_identity),
    ) -> BackendHealthResponse:
        return get_backend_health(identity)

    @app.on_event("shutdown")
    def close_connection() -> None:
        connection.close()

    return app


app = create_app()
