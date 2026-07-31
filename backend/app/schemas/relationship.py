"""
Pydantic schema for dataset relationships.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetRelationshipRead(BaseModel):
    id: str
    left_dataset_id: str
    left_dataset_filename: str
    left_column: str
    right_dataset_id: str
    right_dataset_filename: str
    right_column: str
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, rel) -> "DatasetRelationshipRead":
        """
        Built explicitly (not via automatic from_attributes) since the
        filenames come from the related Dataset objects, not directly
        from columns on DatasetRelationship itself.
        """
        return cls(
            id=rel.id,
            left_dataset_id=rel.left_dataset_id,
            left_dataset_filename=rel.left_dataset.original_filename,
            left_column=rel.left_column,
            right_dataset_id=rel.right_dataset_id,
            right_dataset_filename=rel.right_dataset.original_filename,
            right_column=rel.right_column,
            confidence=rel.confidence,
            created_at=rel.created_at,
        )
