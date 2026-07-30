"""
Upload endpoint.

Kept intentionally thin — this route only handles HTTP concerns (request
parsing, status codes, error translation). All real logic lives in
upload_service.py. This separation is what makes the service layer
testable without needing a running server.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dataset import DatasetRead, ProjectRead, UploadResponse
from app.services.upload_service import UploadValidationError, handle_upload

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=UploadResponse, status_code=201)
def upload_dataset(
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
    project_name: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    Uploads a single file.

    - Pass `project_id` to add this file to an existing project (multi-file upload).
    - Omit `project_id` to create a new project (optionally naming it via `project_name`).
    """
    try:
        project, dataset = handle_upload(db, file, project_id, project_name)
    except UploadValidationError as e:
        # Translate a domain-level error into a proper HTTP response.
        # The service layer doesn't know about HTTP at all — this route
        # is the only place that decides "this becomes a 400".
        raise HTTPException(status_code=400, detail=str(e))

    return UploadResponse(
        project=ProjectRead.model_validate(project),
        dataset=DatasetRead.from_model(dataset),
    )
