import logging
import os
import sqlite3
from pathlib import Path, PurePosixPath

import urllib3
from fastapi import HTTPException, UploadFile

from app.models import (
    CLOSED_TASK_STATUSES,
    HIGH_TASK_PRIORITY,
    BackendHealthResponse,
    CreateTaskRequest,
    Identity,
    RequirementUploadResponse,
    TaskResponse,
    TaskSummaryResponse,
)
from app.repository import TaskRepository

ALLOWED_UPLOAD_EXTENSIONS = frozenset({".txt", ".md", ".pdf"})
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024
UPLOAD_READ_CHUNK_BYTES = 64 * 1024
DEFAULT_AUTH_HEALTH_URL = "http://localhost:8080/q/health"
BACKEND_HEALTH_TIMEOUT_SECONDS = 3.0
BACKEND_HEALTH_ERROR_MESSAGE = "Backend health check failed"
UPLOAD_STORAGE_ERROR_MESSAGE = "Unable to store uploaded file"
logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def list_tasks(
        self,
        identity: Identity,
        requested_owner: str | None,
    ) -> list[TaskResponse]:
        self._ensure_owner_access(identity, requested_owner)
        return [
            task_response(row)
            for row in self.repository.list_for_owner(identity.username)
        ]

    def create_task(
        self,
        identity: Identity,
        request: CreateTaskRequest,
    ) -> TaskResponse:
        self._ensure_owner_access(identity, request.owner)
        row = self.repository.create(
            title=request.title,
            description=request.description,
            status=request.status,
            owner=identity.username,
            priority=request.priority,
        )
        return task_response(row)

    def summary(
        self,
        identity: Identity,
        requested_owner: str | None,
    ) -> TaskSummaryResponse:
        self._ensure_owner_access(identity, requested_owner)
        status_counts: dict[str, int] = {}
        high_priority_open = 0
        rows = self.repository.summary_for_owner(identity.username)
        for row in rows:
            task_status = str(row["status"])
            status_counts[task_status] = status_counts.get(task_status, 0) + 1
            if (
                row["priority"] == HIGH_TASK_PRIORITY
                and task_status not in CLOSED_TASK_STATUSES
            ):
                high_priority_open += 1
        return TaskSummaryResponse(
            owner=identity.username,
            total=sum(status_counts.values()),
            by_status=status_counts,
            high_priority_open=high_priority_open,
        )

    @staticmethod
    def _ensure_owner_access(
        identity: Identity,
        requested_owner: str | None,
    ) -> None:
        if requested_owner and requested_owner != identity.username:
            raise HTTPException(status_code=403, detail="Forbidden")


async def store_requirement(
    file: UploadFile,
    identity: Identity,
    upload_directory: Path,
) -> RequirementUploadResponse:
    filename = _validate_upload_filename(file.filename)
    content = await _read_upload(file)
    target = upload_directory / filename
    try:
        target.write_bytes(content)
    except OSError as error:
        logger.exception("Could not store uploaded requirement")
        raise HTTPException(
            status_code=500,
            detail=UPLOAD_STORAGE_ERROR_MESSAGE,
        ) from error
    return RequirementUploadResponse(
        owner=identity.username,
        file_name=filename,
        stored_at=str(target),
        size=len(content),
    )


def _validate_upload_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid file name")
    normalized_name = PurePosixPath(filename.replace("\\", "/")).name
    if normalized_name != filename or normalized_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid file name")
    if Path(normalized_name).suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    return normalized_name


async def _read_upload(file: UploadFile) -> bytearray:
    content = bytearray()
    while True:
        chunk = await file.read(UPLOAD_READ_CHUNK_BYTES)
        if not chunk:
            return content
        if len(content) + len(chunk) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Uploaded file is too large")
        content.extend(chunk)


def backend_health(
    identity: Identity,
    url: str | None = None,
) -> BackendHealthResponse:
    selected_url = url or os.getenv("AUTH_HEALTH_URL", DEFAULT_AUTH_HEALTH_URL)
    try:
        response = urllib3.PoolManager().request(
            "GET",
            selected_url,
            timeout=BACKEND_HEALTH_TIMEOUT_SECONDS,
        )
        response_body = response.data.decode("utf-8")
    except (urllib3.exceptions.HTTPError, OSError, UnicodeDecodeError):
        logger.exception("Backend health request failed")
        return BackendHealthResponse(
            requested_by=identity.username,
            status=0,
            body=BACKEND_HEALTH_ERROR_MESSAGE,
        )
    return BackendHealthResponse(
        requested_by=identity.username,
        status=response.status,
        body=response_body,
    )


def task_response(row: sqlite3.Row) -> TaskResponse:
    return TaskResponse(
        id=int(row["id"]),
        title=str(row["title"]),
        description=str(row["description"]),
        status=str(row["status"]),
        owner=str(row["owner"]),
        priority=str(row["priority"]),
        created_at=str(row["created_at"]),
    )
