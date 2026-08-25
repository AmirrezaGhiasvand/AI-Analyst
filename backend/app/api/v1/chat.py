"""
Chat endpoint.

Top-level (not nested under /projects/{id}) since project_id is now
optional — a chat message can be the very first action that creates a
project, mirroring how upload works. Endpoints that only ever operate
on an EXISTING project (relationships, report) stay under /projects/{id}.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ask_question, ProjectNotFoundError

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Sends a message. Omit project_id to start a new project (optionally
    named via project_name); provide project_id to continue an existing
    project's conversation.
    """
    try:
        result = ask_question(
            db, question=request.question,
            project_id=request.project_id, project_name=request.project_name,
        )
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ChatResponse.from_message(
        project=result["project"], message=result["message"],
        route=result["route"], execution_result=result["execution_result"],
        report_url=result["report_url"],
    )