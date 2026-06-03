# Euphoriam AI (Python)

Stage 1 LLM service: **Coach**, **Map Resistance**, **domain structure extraction**, **member emails**, and **Plan A lead post-diagnostic emails**.

Node (`euphoriam-backend`) owns auth, DB, and REST; this service owns generation.

## Run locally

### Mac / Linux

```bash
cd euphoriam-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # set OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Windows

```bash
cd euphoriam-ai
python -m venv .venv
.venv\Scripts\activate
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
USE_PYTHON_MEMBER_EMAIL=true
USE_PYTHON_LEAD_EMAIL=true
```

Restart Node after changing flags.

**Member emails:** Node builds `member_context` (DB, Stage 1, coach history). Python only runs the LLM (`POST /v1/member-email/generate`) using the Nathan prompt loaded from Node/Postgres.

## API (called by Node)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/coach/reply` | Daily coach check-in |
| POST | `/v1/coach/friction` | Friction rescue |
| POST | `/v1/map-resistance/turn` | Map Resistance Q&A turn |
| POST | `/v1/map-resistance/finalize` | Extract structure after mapping |
| POST | `/v1/extraction/domain-structure` | Same extraction (alias) |
| POST | `/v1/member-email/generate` | Personalised structural member email (LLM only) |
| POST | `/v1/lead-email/generate` | Plan A post-diagnostic lead email (LLM only) |

See [euphoriam-backend/docs/PYTHON-AI-IMPLEMENTATION.md](../euphoriam-backend/docs/PYTHON-AI-IMPLEMENTATION.md) and [PLAN-A-LEAD-NURTURE.md](../euphoriam-backend/docs/PLAN-A-LEAD-NURTURE.md).

## Responsibility split (member + lead email)

| Layer | Service |
|-------|---------|
| Context, quotes, proof bar, validation, Brevo send, logs, cron, admin APIs | **Node** (`euphoriam-backend`) |
| OpenAI JSON generation + retry payload | **Python** (`euphoriamAi-python`) |
