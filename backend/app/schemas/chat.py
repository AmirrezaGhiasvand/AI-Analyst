"""
Pydantic schemas for the chat endpoint.
"""

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    message_id: str
    role: str
    content: str
    generated_code: str | None = None
    route: str | None = None
    execution_result: Any | None = None
    chart: dict | None = None
    created_at: datetime

    @classmethod
    def from_message(
        cls, message, route: str | None, execution_result: Any
    ) -> "ChatResponse":
        chart = json.loads(message.chart_json) if message.chart_json else None
        return cls(
            message_id=message.id,
            role=message.role,
            content=message.content,
            generated_code=message.generated_code,
            route=route,
            execution_result=execution_result,
            chart=chart,
            created_at=message.created_at,
        )
