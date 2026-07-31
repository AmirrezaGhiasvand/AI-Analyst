"""
DatasetRelationship model.

Represents a detected (or later, user-confirmed) join relationship
between a column in one dataset and a column in another — e.g.
orders.customer_id <-> customers.id. Belongs to neither dataset alone,
so it gets its own table rather than living as a column on Dataset.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset


def _uuid() -> str:
    return str(uuid.uuid4())


class DatasetRelationship(Base):
    __tablename__ = "dataset_relationships"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)

    left_dataset_id: Mapped[str] = mapped_column(String, ForeignKey("datasets.id"))
    left_column: Mapped[str] = mapped_column(String)

    right_dataset_id: Mapped[str] = mapped_column(String, ForeignKey("datasets.id"))
    right_column: Mapped[str] = mapped_column(String)

    # 0.0-1.0 — how confident the detector is this is a real relationship,
    # based on value overlap between the two columns. Stored (not just
    # thresholded away) so the UI can show "likely" vs "strong" matches.
    confidence: Mapped[float] = mapped_column(Float)

    # "join": a normal foreign-key-style relationship between two
    # different tables (e.g. orders.customer_id -> customers.id).
    # "possible_duplicate": nearly every column between the two datasets
    # matched — a sign these are two overlapping exports of the same
    # data, not genuinely different tables that should be joined.
    relationship_type: Mapped[str] = mapped_column(String, default="join")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    left_dataset: Mapped["Dataset"] = relationship(
        "Dataset", foreign_keys=[left_dataset_id]
    )
    right_dataset: Mapped["Dataset"] = relationship(
        "Dataset", foreign_keys=[right_dataset_id]
    )
