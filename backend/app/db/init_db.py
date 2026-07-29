"""
Creates all DB tables from the current models.

Run manually during early development: `python -m app.db.init_db`
Once the schema stabilizes, this will be replaced by Alembic migrations,
which support altering existing tables without data loss.
"""

import app.models  # noqa: F401  (registers models on Base.metadata)
from app.db.session import Base, engine


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    init_db()
