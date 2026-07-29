"""
Project model.

A Project is created when a user uploads one or more datasets. It's the
anchor for everything else: datasets, chat memory, and reports are all
scoped to a project, never global. This matches our design decision that
conversational memory should live inside a project, not across the app.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False, default="Untitled Project")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # cascade="all, delete-orphan": deleting a project cleans up its
    # datasets automatically instead of leaving orphaned rows behind.
    datasets = relationship(
        "Dataset", back_populates="project", cascade="all, delete-orphan"
    )
