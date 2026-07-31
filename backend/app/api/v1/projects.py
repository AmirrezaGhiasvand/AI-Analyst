"""
Project-level endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project
from app.models.relationship import DatasetRelationship
from app.schemas.dataset import ProjectRead, ProjectWithDatasets
from app.schemas.relationship import DatasetRelationshipRead

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    """Returns all projects, most recently updated first."""
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    return projects


@router.get("/{project_id}", response_model=ProjectWithDatasets)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Returns a single project along with all its datasets."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=404, detail=f"Project '{project_id}' not found."
        )
    return ProjectWithDatasets.from_model(project)


@router.get("/{project_id}/relationships", response_model=list[DatasetRelationshipRead])
def list_relationships(project_id: str, db: Session = Depends(get_db)):
    """
    Returns all detected relationships between datasets in a project.
    Detection itself runs automatically after each upload — this endpoint
    just reads the current results.
    """
    relationships = (
        db.query(DatasetRelationship)
        .filter(DatasetRelationship.left_dataset.has(project_id=project_id))
        .all()
    )
    return [DatasetRelationshipRead.from_model(r) for r in relationships]
