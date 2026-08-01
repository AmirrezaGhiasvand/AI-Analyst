"""
Pydantic schemas for the chat endpoint.
"""

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
    created_at: datetime
