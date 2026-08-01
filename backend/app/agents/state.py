"""
Shared agent state.

LangGraph passes one state object through every node in the graph. Each
node reads what it needs and returns updates to merge back in. Keeping
this as an explicit, typed schema (rather than a loose dict) makes the
data flowing through the graph self-documenting.
"""

from typing import Any, TypedDict


class DatasetContext(TypedDict):
    """What the Planner/Analyst see about one dataset — enough to reason
    about it, without re-reading the raw file."""

    id: str
    filename: str
    file_type: str
    storage_path: str
    row_count: int
    column_count: int
    columns: dict  # column_name -> {"kind": ..., "null_count": ..., ...}


class AgentState(TypedDict):
    project_id: str
    question: str
    conversation_history: list[
        dict[str, str]
    ]  # [{"role": "user"|"assistant", "content": "..."}]
    dataset_context: list[DatasetContext]

    # Set by the Planner
    route: str | None  # "direct" | "analyze"
    target_dataset_id: str | None

    # Set by the Analyst
    generated_code: str | None
    execution_result: Any | None
    analysis_error: str | None

    # Final output
    final_answer: str | None
