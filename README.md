# AI Support Ticket Chatbot

Production-oriented backend for a support assistant that retrieves historical tickets, ranks them with hybrid retrieval, and generates actionable answers with RAG.

## What is implemented

- FastAPI modular monolith with Clean Architecture layers
- Structured retrieval (keywords, error codes, tags)
- Semantic retrieval with `pgvector` + OpenAI embeddings
- Hybrid ranking (text score + semantic score)
- RAG endpoint with internal ticket grounding
- Ticket ingestion endpoint with optional auto-embedding
- Embedding reindex endpoint and CLI script
- Retrieval baseline evaluation script + labeled dataset
- Hybrid weight tuning script
- API key auth (optional), in-memory rate limiting, runtime metrics endpoint
- Browser demo endpoint for portfolio showcase
- Alembic migrations, seed data, tests, CI workflow

## Stack

- Python 3.12+
- FastAPI
- PostgreSQL 16 + pgvector
- SQLAlchemy 2 + Alembic
- OpenAI API (`openai` SDK)
- Docker / Docker Compose
- Pytest + Ruff

## Architecture

```text
app/
  api/              # HTTP routers and dependency wiring
  application/      # Use cases, services, contracts
  domain/           # Entities and value objects
  infrastructure/   # DB, repositories, OpenAI adapters, config
  schemas/          # API request/response contracts
  scripts/          # Operational scripts (seed/reindex)
```

## Key endpoints

- `GET /health`
- `GET /api/v1/tickets`
- `POST /api/v1/tickets`
- `GET /api/v1/tickets/search?query=...&limit=...&categoria=...&estado=...`
- `POST /api/v1/tickets/embeddings/reindex?limit=50&only_missing=true`
- `POST /api/v1/chat/ask`
- `GET /api/v1/ops/metrics`
- `GET /demo`

## Local setup

1. Configure environment:

```bash
cp .env.example .env
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start PostgreSQL:

```bash
docker compose up -d postgres
```

3. Run migrations:

```bash
alembic upgrade head
```

4. Seed demo tickets:

```bash
python -m app.scripts.seed_tickets
```

5. (Optional) Generate embeddings:

```bash
python -m app.scripts.reindex_embeddings --limit 200 --only-missing
```

6. Run API:

```bash
uvicorn app.main:app --reload
```

Swagger:

- `http://127.0.0.1:8000/docs`

Demo UI:

- `http://127.0.0.1:8000/demo`

## Run with Docker Compose (API + DB)

```bash
docker compose up -d --build
```

The container entrypoint runs:

- `alembic upgrade head`
- `python -m app.scripts.seed_tickets`
- `uvicorn app.main:app`

## Example: RAG request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Users get ERR-401 when logging into the support portal",
    "top_k": 5
  }'
```

## Embedding and hybrid retrieval notes

- Ticket rows store `embedding vector(1536)` in PostgreSQL.
- Semantic search uses cosine similarity through pgvector.
- Final ranking score is:

```text
hybrid_score = text_weight * normalized_text_score + semantic_weight * semantic_score
```

Weights are configurable in `.env`:

- `HYBRID_TEXT_WEIGHT`
- `HYBRID_SEMANTIC_WEIGHT`

You can tune weights from dataset:

```bash
python -m app.scripts.tune_hybrid_weights --k 5 --json-output evaluation/reports/tuning.json
```

## Testing

```bash
pytest -q
```

Retrieval baseline evaluation:

```bash
python -m app.scripts.evaluate_retrieval --mode api --k 5 --json-output evaluation/reports/baseline.json
```

Integration test is opt-in:

```bash
RUN_INTEGRATION_TESTS=1 DATABASE_URL=... pytest -q -m integration
```

## CI

GitHub Actions workflow runs:

- `ruff check .`
- `pytest -q -m "not integration"`

## Important environment variables

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSION`
- `SEMANTIC_SEARCH_ENABLED`
- `SEARCH_CANDIDATE_LIMIT`
- `SEMANTIC_CANDIDATE_LIMIT`
- `CHAT_MAX_CONTEXT_TICKETS`
- `RERANK_ENABLED`
- `RERANK_WINDOW`
- `API_KEY_REQUIRED`
- `INTERNAL_API_KEY`
- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_REQUESTS`
- `RATE_LIMIT_WINDOW_SECONDS`

## Deployment

Render deployment template is included:

- `render.yaml`

## Current prioritization rule

Internal knowledge base is always prioritized. If OpenAI is unavailable, the system falls back to deterministic internal response generation and still returns ranked source tickets.
