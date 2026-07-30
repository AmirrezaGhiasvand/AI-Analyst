"""
Dataset model.

Represents a single uploaded file within a Project. Multiple datasets can
belong to one project (our multi-file upload requirement) — relationship
detection between datasets happens later, in the profiling/relationship
section, not here.

Uses SQLAlchemy 2.0's typed declarative style (Mapped/mapped_column) —
see project.py for why.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    # Only imported for type checking, never at runtime — avoids a
    # circular import with project.py, which imports Dataset the same way.
    from app.models.project import Project


def _uuid() -> str:
    return str(uuid.uuid4())


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))

    original_filename: Mapped[str] = mapped_column(String)
    # Path on disk where the raw file is stored. Kept separate from
    # original_filename since we store files under a generated name to
    # avoid collisions/path traversal issues (see upload service).
    storage_path: Mapped[str] = mapped_column(String)

    file_type: Mapped[str] = mapped_column(String)  # csv, xlsx, json, parquet
    size_bytes: Mapped[int] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String, default="uploaded")
    # uploaded -> profiling -> ready -> failed

    # Filled in by the profiling step. Flat columns for cheap
    # querying/display; detailed per-column stats go in `profile_json`
    # since that shape varies per dataset and isn't queried via SQL.
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    profile_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    profiling_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped["Project"] = relationship("Project", back_populates="datasets")
