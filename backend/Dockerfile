FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# The backend imports from database/, data/, and ml/ as sibling top-level
# packages (see pytest.ini's `pythonpath = .` for the same convention in
# tests) — the whole repo, not just backend/, is the build context.
COPY backend /app/backend
COPY database /app/database
COPY data /app/data
COPY ml /app/ml
COPY alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
