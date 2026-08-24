"""
Chat service.

The bridge between the database and the agent graph: loads a project's
dataset context and recent conversation history, runs the graph, and
persists both the user's message and the agent's response.

project_id is now optional here, mirroring the upload flow: if omitted,
a new project is created on the fly. This lets a chat conversation be
the very first thing a user does, without a separate upload step first
(useful for pure Q&A sessions, or once dataset upload happens through
other means) — same "create if missing, reuse if given" pattern as
upload_service.handle_upload.
"""

import json

from sqlalchemy.orm import Session

from app.agents.graph import agent_graph
from app.agents.state import AgentState, DatasetContext
from app.models.conversation import Conversation
from app.models.dataset import Dataset
from app.models.message import Message
from app.models.project import Project

HISTORY_LIMIT = 20


class ProjectNotFoundError(Exception):
    """Raised when an explicit project_id is given but doesn't exist.
    Caught in the route layer and turned into an HTTP 404."""


def _get_or_create_project(db: Session, project_id: str | None, project_name: str | None) -> Project:
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            raise ProjectNotFoundError(f"Project '{project_id}' not found.")
        return project

    project = Project(name=project_name or "Untitled Project")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _get_or_create_conversation(db: Session, project_id: str) -> Conversation:
    conversation = db.query(Conversation).filter(Conversation.project_id == project_id).first()
    if conversation is None:
        conversation = Conversation(project_id=project_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


def _build_dataset_context(db: Session, project_id: str) -> list[DatasetContext]:
    ready_datasets = (
        db.query(Dataset)
        .filter(Dataset.project_id == project_id, Dataset.status == "ready")
        .all()
    )

    context: list[DatasetContext] = []
    for ds in ready_datasets:
        profile = json.loads(ds.profile_json) if ds.profile_json else {}
        context.append(
            DatasetContext(
                id=ds.id, filename=ds.original_filename, file_type=ds.file_type,
                storage_path=ds.storage_path, row_count=ds.row_count or 0,
                column_count=ds.column_count or 0, columns=profile.get("columns", {}),
            )
        )
    return context


def _load_history(db: Session, conversation_id: str) -> list[dict[str, str]]:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    messages.reverse()
    return [{"role": m.role, "content": m.content} for m in messages]


def ask_question(
    db: Session,
    question: str,
    project_id: str | None = None,
    project_name: str | None = None,
) -> dict:
    """
    Runs one full turn. If project_id is omitted, a new project is
    created first (same pattern as upload). Returns the project used/
    created alongside the assistant's response, since the caller needs
    the project_id for subsequent messages if one wasn't provided.
    """
    project = _get_or_create_project(db, project_id, project_name)

    conversation = _get_or_create_conversation(db, project.id)
    history = _load_history(db, conversation.id)
    dataset_context = _build_dataset_context(db, project.id)

    user_message = Message(conversation_id=conversation.id, role="user", content=question)
    db.add(user_message)
    db.commit()

    initial_state: AgentState = {
        "project_id": project.id,
        "question": question,
        "conversation_history": history,
        "dataset_context": dataset_context,
        "route": None,
        "target_dataset_id": None,
        "generated_code": None,
        "execution_result": None,
        "analysis_error": None,
        "chart_json": None,
        "final_answer": None,
    }

    result_state = agent_graph.invoke(initial_state)

    final_answer = result_state.get("final_answer") or "I wasn't able to generate a response."
    generated_code = result_state.get("generated_code")
    execution_result = result_state.get("execution_result")
    chart_json = result_state.get("chart_json")

    assistant_message = Message(
        conversation_id=conversation.id, role="assistant", content=final_answer,
        generated_code=generated_code, chart_json=chart_json,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "project": project,
        "message": assistant_message,
        "route": result_state.get("route"),
        "execution_result": execution_result,
    }