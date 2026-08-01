"""
Chat service.

The bridge between the database and the agent graph: loads a project's
dataset context and recent conversation history, runs the graph, and
persists both the user's message and the agent's response. This is
where "memory" actually happens — it's just rows in the messages table,
loaded into the graph's starting state each turn. No hidden state.
"""

import json

from app.agents.graph import agent_graph
from app.agents.state import AgentState, DatasetContext
from app.models.conversation import Conversation
from app.models.dataset import Dataset
from app.models.message import Message
from sqlalchemy.orm import Session

# How many prior messages to include as context for each new question.
# Bounded so conversations don't grow the prompt unboundedly over time.
HISTORY_LIMIT = 20


def _get_or_create_conversation(db: Session, project_id: str) -> Conversation:
    conversation = (
        db.query(Conversation).filter(Conversation.project_id == project_id).first()
    )
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
                id=ds.id,
                filename=ds.original_filename,
                file_type=ds.file_type,
                storage_path=ds.storage_path,
                row_count=ds.row_count or 0,
                column_count=ds.column_count or 0,
                columns=profile.get("columns", {}),
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
    # Reverse back to chronological order (query above was newest-first
    # to make LIMIT cheap, but the LLM needs oldest-first).
    messages.reverse()
    return [{"role": m.role, "content": m.content} for m in messages]


def ask_question(db: Session, project_id: str, question: str) -> dict:
    """
    Runs one full turn: persists the user's message, runs the agent
    graph, persists the assistant's response, and returns it.
    """
    conversation = _get_or_create_conversation(db, project_id)

    history = _load_history(db, conversation.id)
    dataset_context = _build_dataset_context(db, project_id)

    user_message = Message(
        conversation_id=conversation.id, role="user", content=question
    )
    db.add(user_message)
    db.commit()

    initial_state: AgentState = {
        "project_id": project_id,
        "question": question,
        "conversation_history": history,
        "dataset_context": dataset_context,
        "route": None,
        "target_dataset_id": None,
        "generated_code": None,
        "execution_result": None,
        "analysis_error": None,
        "final_answer": None,
    }

    result_state = agent_graph.invoke(initial_state)

    final_answer = (
        result_state.get("final_answer") or "I wasn't able to generate a response."
    )
    generated_code = result_state.get("generated_code")
    execution_result = result_state.get("execution_result")

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=final_answer,
        generated_code=generated_code,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "message": assistant_message,
        "route": result_state.get("route"),
        "execution_result": execution_result,
    }
