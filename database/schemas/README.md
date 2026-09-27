# Schemas (reserved)

The database schema itself lives in `database/models/` (SQLAlchemy ORM
classes, the actual source of truth) and `database/migrations/` (Alembic).
This directory is reserved for standalone schema artifacts if they become
useful later — e.g. an exported JSON Schema for API payload validation
shared with a non-Python client, or an ER diagram export. Nothing here
yet; see [docs/DATABASE.md](../../docs/DATABASE.md) for the current
schema reference.
