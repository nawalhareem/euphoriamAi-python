# Euphoriam AI: FastAPI LLM service for Render (and other Docker hosts).
# Render sets PORT automatically; bind to 0.0.0.0.
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy dependency manifest first for better layer caching
COPY requirements.txt .

RUN python -m venv /app/venv \
    && . /app/venv/bin/activate \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Application source
COPY . .

ENV PORT=8000
EXPOSE 8000

# Health: GET /health
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
