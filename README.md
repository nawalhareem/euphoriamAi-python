# Euphoriam AI (Python)

Stage 1 LLM service: **Coach**, **Map Resistance**, and **domain structure extraction**.

Node (`euphoriam-backend`) owns auth, DB, and REST; this service owns generation.

## Run locally

```bash
cd euphoriam-ai
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env     # set OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

Health: http://localhost:8000/health

## Node integration

In `euphoriam-backend/.env`:

```env
AI_SERVICE_URL=http://localhost:8000
USE_PYTHON_COACH=true
USE_PYTHON_MAP_RESISTANCE=true
```

Restart Node after changing flags.

## API (called by Node)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/coach/reply` | Daily coach check-in |
| POST | `/v1/coach/friction` | Friction rescue |
| POST | `/v1/map-resistance/turn` | Map Resistance Q&A turn |
| POST | `/v1/map-resistance/finalize` | Extract structure after mapping |
| POST | `/v1/extraction/domain-structure` | Same extraction (alias) |

See [euphoriam-backend/docs/PYTHON-AI-IMPLEMENTATION.md](../euphoriam-backend/docs/PYTHON-AI-IMPLEMENTATION.md).
