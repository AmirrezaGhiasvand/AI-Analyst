import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Float
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
    confidence: Mapped[float] = mapped_column(Float)
    relationship_type: Mapped[str] = mapped_column(String, default="join")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    left_dataset: Mapped["Dataset"] = relationship("Dataset", foreign_keys=[left_dataset_id])
    right_dataset: Mapped["Dataset"] = relationship("Dataset", foreign_keys=[right_dataset_id])