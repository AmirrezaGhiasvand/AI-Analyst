"""
Upload service.

Contains the actual business logic for handling a file upload: validation,
safe storage on disk, profiling, and creating/updating the Project/Dataset
DB records. Kept separate from the API route so this logic is testable
and reusable (e.g., agents could trigger uploads programmatically later
without going through HTTP).
"""

import json
import uuid
from pathlib import Path

from app.core.config import settings
from app.models.dataset import Dataset
from app.models.project import Project
from app.services.profiling_service import ProfilingError, profile_dataset
from app.services.relationship_service import detect_relationships
from fastapi import UploadFile
from sqlalchemy.orm import Session

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet"}


class UploadValidationError(Exception):
    """Raised when an uploaded file fails validation. Caught in the route
    layer and turned into a proper HTTP 400 response."""


def _validate_file(file: UploadFile, size_bytes: int) -> str:
    """Returns the validated file extension, or raises UploadValidationError."""
    ext = Path(file.filename or "").suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if size_bytes == 0:
        raise UploadValidationError("Uploaded file is empty.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise UploadValidationError(
            f"File exceeds max upload size of {settings.max_upload_size_mb}MB."
        )

    return ext


def _safe_storage_path(dataset_id: str, ext: str) -> str:
    """
    Generates a storage path using a generated UUID, never the user's
    original filename. This avoids path traversal (e.g. '../../etc/passwd')
    and filename collisions between different uploads.
    """
    storage_dir = Path(settings.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    return str(storage_dir / f"{dataset_id}{ext}")


def handle_upload(
    db: Session,
    file: UploadFile,
    project_id: str | None,
    project_name: str | None,
) -> tuple[Project, Dataset]:
    """
    Handles one uploaded file end-to-end:
    1. Validate it
    2. Reuse an existing project or create a new one
    3. Save the file to disk under a safe generated name
    4. Create the Dataset record
    5. Profile it synchronously and update status accordingly
    """
    raw_bytes = file.file.read()
    size_bytes = len(raw_bytes)

    ext = _validate_file(file, size_bytes)

    # Reuse project if an id was passed (adding a file to an existing
    # project); otherwise create a new one — this is what makes multi-file
    # upload into the same project possible.
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            raise UploadValidationError(f"Project '{project_id}' not found.")
    else:
        project = Project(name=project_name or "Untitled Project")
        db.add(project)
        db.flush()  # assigns project.id without committing yet

    dataset_id = str(uuid.uuid4())
    storage_path = _safe_storage_path(dataset_id, ext)

    with open(storage_path, "wb") as f:
        f.write(raw_bytes)

    dataset = Dataset(
        id=dataset_id,
        project_id=project.id,
        original_filename=file.filename,
        storage_path=storage_path,
        file_type=ext.lstrip("."),
        size_bytes=size_bytes,
        status="profiling",
    )
    db.add(dataset)
    db.flush()  # assigns relationships without finalizing the transaction

    # Profiling failure should NOT lose the upload — the file is still
    # saved and the dataset row still exists, just marked as failed with
    # a reason, so the user can see what went wrong instead of the upload
    # silently disappearing.
    try:
        profile = profile_dataset(dataset)
        dataset.row_count = profile["row_count"]
        dataset.column_count = profile["column_count"]
        dataset.profile_json = json.dumps(
            {"columns": profile["columns"], "preview_rows": profile["preview_rows"]}
        )
        dataset.status = "ready"
    except ProfilingError as e:
        dataset.status = "failed"
        dataset.profiling_error = str(e)

    db.commit()
    db.refresh(project)
    db.refresh(dataset)

    # Relationship detection needs this dataset's profile to already be
    # committed (it re-reads profile_json), and only makes sense if
    # profiling actually succeeded. A failure here shouldn't fail the
    # whole upload — the file is still safely uploaded and profiled either way.
    if dataset.status == "ready":
        try:
            detect_relationships(db, project.id)
        except Exception:
            # Relationship detection is a "nice to have" enhancement, not
            # part of the upload's core guarantee. We deliberately swallow
            # errors here rather than let a detection bug fail an otherwise
            # successful upload. Proper logging will replace this silent
            # pass once we add structured logging in a later section.
            pass

    return project, dataset
