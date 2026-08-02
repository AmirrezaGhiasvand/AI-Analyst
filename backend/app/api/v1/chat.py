"""
Chat endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ask_question

router = APIRouter(prefix="/projects", tags=["chat"])


@router.post("/{project_id}/chat", response_model=ChatResponse)
def chat(project_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=404, detail=f"Project '{project_id}' not found."
        )

    result = ask_question(db, project_id, request.question)
    message = result["message"]

    return ChatResponse.from_message(
        message, route=result["route"], execution_result=result["execution_result"]
    )
