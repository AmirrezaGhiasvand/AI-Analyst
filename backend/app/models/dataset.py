"""
Dataset model.

Represents a single uploaded file within a Project. Multiple datasets can
belong to one project (our multi-file upload requirement) — relationship
detection between datasets happens later, in the profiling/relationship
section, not here.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)

    original_filename = Column(String, nullable=False)
    # Path on disk where the raw file is stored. Kept separate from
    # original_filename since we store files under a generated name to
    # avoid collisions/path traversal issues (see upload service).
    storage_path = Column(String, nullable=False)

    file_type = Column(String, nullable=False)  # csv, xlsx, json, parquet
    size_bytes = Column(Integer, nullable=False)

    # Profiling results (row count, schema, etc.) get filled in by the
    # next section — nullable for now since upload happens before profiling.
    status = Column(String, nullable=False, default="uploaded")
    # uploaded -> profiling -> ready -> failed

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="datasets")
