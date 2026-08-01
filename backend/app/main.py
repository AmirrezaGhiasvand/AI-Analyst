"""
Application entrypoint.

Route modules are intentionally NOT imported/included yet — this is the
scaffolding milestone only. Each future section (upload, chat, reports...)
will register its own router under app/api/v1/ and be wired in here.
"""

from fastapi import FastAPI

from app.api.v1 import chat, projects, uploads
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(uploads.router, prefix=settings.api_v1_prefix)
app.include_router(projects.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health_check():
    """Basic liveness check — confirms the server is up and config loads."""
    return {"status": "ok", "app": settings.app_name}
