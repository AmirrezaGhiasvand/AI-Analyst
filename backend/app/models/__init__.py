"""
Importing models here ensures they're registered on Base.metadata before
create_all() (or Alembic) runs. Without this, SQLAlchemy wouldn't know
these tables exist yet.
"""

from app.models.conversation import Conversation  # noqa: F401
from app.models.dataset import Dataset  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.relationship import DatasetRelationship  # noqa: F401
