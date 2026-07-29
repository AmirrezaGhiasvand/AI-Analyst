"""
Pydantic schemas for datasets.

These define the exact shape of API requests/responses. FastAPI uses
these to auto-generate OpenAPI docs — this file IS the contract your
frontend integrates against, so field names/types here should be treated
as stable once the frontend starts consuming them.
"""

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
    created_at: datetime

    # Lets Pydantic build this model directly from a SQLAlchemy object
    # (model.id, model.project_id, ...) instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)


class ProjectRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    """Returned immediately after a successful upload."""

    project: ProjectRead
    dataset: DatasetRead
