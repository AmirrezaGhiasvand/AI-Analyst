"""
Shared agent state.
"""

from typing import TypedDict, Optional, Any


class DatasetContext(TypedDict):
    id: str
    filename: str
    file_type: str
    storage_path: str
    row_count: int
    column_count: int
    columns: dict


class AgentState(TypedDict):
    project_id: str
    question: str
    conversation_history: list[dict[str, str]]
    dataset_context: list[DatasetContext]

    route: Optional[str]
    target_dataset_id: Optional[str]

    generated_code: Optional[str]
    execution_result: Optional[Any]
    analysis_error: Optional[str]

    chart_json: Optional[str]

    final_answer: Optional[str]