"""
Pydantic schemas for the chat endpoint.
"""

import json
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    # Mirrors the upload endpoint's pattern: omit project_id to create a
    # new project (optionally naming it via project_name); provide it to
    # continue an existing project's conversation.
    project_id: Optional[str] = None
    project_name: Optional[str] = None


class ProjectInfo(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    project: ProjectInfo
    message_id: str
    role: str
    content: str
    generated_code: Optional[str] = None
    route: Optional[str] = None
    execution_result: Optional[Any] = None
    chart: Optional[dict] = None
    report_url: Optional[str] = None
    created_at: datetime

    @classmethod
    def from_message(
        cls, project, message, route: Optional[str], execution_result: Any,
        report_url: Optional[str] = None,
    ) -> "ChatResponse":
        chart = json.loads(message.chart_json) if message.chart_json else None
        return cls(
            project=ProjectInfo.model_validate(project),
            message_id=message.id,
            role=message.role,
            content=message.content,
            generated_code=message.generated_code,
            route=route,
            execution_result=execution_result,
            chart=chart,
            report_url=report_url,
            created_at=message.created_at,
        )