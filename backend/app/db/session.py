"""
Database engine and session management.

We use SQLAlchemy's declarative ORM so models are defined once in
app/models/ and reused across services, agents, and the API layer.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# check_same_thread=False is required for SQLite when used with FastAPI's
# threaded request handling. This restriction doesn't apply to Postgres,
# so this line simply becomes a no-op if we switch later.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a DB session per-request and
    guarantees it's closed afterward, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
