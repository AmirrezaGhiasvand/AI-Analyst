"""
Project model.

A Project is created when a user uploads one or more datasets. It's the
anchor for everything else: datasets, chat memory, and reports are all
scoped to a project, never global. This matches our design decision that
conversational memory should live inside a project, not across the app.

Uses SQLAlchemy 2.0's typed declarative style (Mapped/mapped_column)
instead of plain Column(...) — this gives instance attributes their real
Python types (str, not Column[str]) as far as static type checkers are
concerned.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    # Only imported for type checking, never at runtime — avoids a
    # circular import with dataset.py, which imports Project the same way.
    from app.models.dataset import Dataset


def _uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, default="Untitled Project")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # cascade="all, delete-orphan": deleting a project cleans up its
    # datasets automatically instead of leaving orphaned rows behind.
    datasets: Mapped[list["Dataset"]] = relationship(
        "Dataset", back_populates="project", cascade="all, delete-orphan"
    )
