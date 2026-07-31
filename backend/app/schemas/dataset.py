"""
Pydantic schemas for datasets.

These define the exact shape of API requests/responses. FastAPI uses
these to auto-generate OpenAPI docs — this file IS the contract your
frontend integrates against, so field names/types here should be treated
as stable once the frontend starts consuming them.
"""

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetRead(BaseModel):
    """What the API returns after an upload (or when listing datasets)."""

    id: str
    project_id: str
    original_filename: str
    file_type: str
    size_bytes: int
    status: str
    row_count: int | None = None
    column_count: int | None = None
    profile: dict | None = None
    profiling_error: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, dataset) -> "DatasetRead":
        """
        Builds this schema from a Dataset ORM object, parsing the stored
        profile_json string into a real dict. Done explicitly here (rather
        than relying on automatic from_attributes mapping) since the DB
        column name (profile_json) and API field name (profile) differ,
        and the DB stores it as a string that needs parsing either way.
        """
        profile = json.loads(dataset.profile_json) if dataset.profile_json else None
        return cls(
            id=dataset.id,
            project_id=dataset.project_id,
            original_filename=dataset.original_filename,
            file_type=dataset.file_type,
            size_bytes=dataset.size_bytes,
            status=dataset.status,
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            profile=profile,
            profiling_error=dataset.profiling_error,
            created_at=dataset.created_at,
        )


class ProjectRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectWithDatasets(BaseModel):
    """Returned when fetching a single project — includes its datasets
    so the frontend (and you, for debugging) can see everything in one call."""

    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    datasets: list[DatasetRead]

    @classmethod
    def from_model(cls, project) -> "ProjectWithDatasets":
        return cls(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            updated_at=project.updated_at,
            datasets=[DatasetRead.from_model(d) for d in project.datasets],
        )


class UploadResponse(BaseModel):
    """Returned immediately after a successful upload."""

    project: ProjectRead
    dataset: DatasetRead
