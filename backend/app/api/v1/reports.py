"""
Report endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project
from app.services.report_service import generate_report_pdf

router = APIRouter(prefix="/projects", tags=["reports"])


@router.get("/{project_id}/report")
def get_report(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=404, detail=f"Project '{project_id}' not found."
        )

    pdf_bytes = generate_report_pdf(db, project_id)

    safe_filename = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in project.name
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}_report.pdf"'
        },
    )
