# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MarketPulse AI is a real-time financial sentiment intelligence platform. It aggregates content from Reddit, News RSS, and StockTwits, runs FinBERT + Claude Haiku ensemble sentiment scoring, and surfaces insights via a Next.js dashboard.

## Development Commands

### Start Full Stack (recommended)
```bash
docker-compose up
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/api/v1/health

### Backend (direct)
```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload        # Start dev server
alembic upgrade head                  # Apply DB migrations
python app/seed.py                    # Seed industries + companies
```

### Frontend (direct)
```bash
cd frontend
npm install
npm run dev
```

### Testing
```bash
cd backend
pytest                                # Run all tests
pytest tests/test_api.py::test_name  # Run single test
```

## Architecture

### Request Flow
Frontend (`apiFetch` in `src/lib/api.ts`) → FastAPI (`/api/v1/*`) → PostgreSQL (via async SQLAlchemy) + Redis (cache)

All API routes are registered in `backend/app/api/router.py` and mounted at `/api/v1` in `main.py`.

### Backend Structure (`backend/app/`)
- `main.py` — FastAPI app, lifespan (Redis cleanup), CORS middleware
- `config.py` — Pydantic Settings, all env vars
- `core/` — `database.py` (async SQLAlchemy engine, pool 5/10), `redis.py` (global async client)
- `dependencies.py` — FastAPI `get_db()` and `get_cache()` dependencies
- `models/` — 11 SQLAlchemy ORM models (all use UUID PKs via `gen_random_uuid()`)
- `schemas/` — Pydantic request/response schemas for each domain (company, industry, sentiment, analyst, analytics, graph)
- `api/` — Route handlers: `industries`, `companies`, `sentiment`, `analytics`, `analyst`, `graph`
- `seed.py` — Populates 10 industries, 36 companies with aliases

**Implemented backend modules:**
- `ingestion/` — `service.py` orchestrates collectors; `reddit_collector.py`, `news_collector.py`, `stocktwits_collector.py`; `scheduler.py` (APScheduler)
- `processing/` — `pipeline.py` → `entity_extractor.py`, `company_mapper.py`, `deduplicator.py`, `text_cleaner.py`
- `sentiment/` — `ensemble.py` combines `finbert.py` + `llm_scorer.py`; `explainability.py`
- `analytics/` — `aggregator.py`, `anomaly_detector.py`, `momentum.py`, `confidence.py`, `predictive.py`, `cross_source.py`
- `analyst/` — `briefing_generator.py`, `company_summarizer.py`, `risk_alerts.py`, `prompts.py`
- `market/` — `price_fetcher.py` (yfinance)

### Debug Endpoints (development only)
When `ENVIRONMENT=development`, these POST endpoints are registered under `/api/v1/debug/`:
- `POST /debug/ingest/{source}` — trigger single source ingestion
- `POST /debug/ingest` — trigger all collectors
- `POST /debug/process` — run sentiment processing pipeline
- `POST /debug/analytics` — full analytics pipeline (aggregate → momentum → confidence → anomalies)
- `POST /debug/prices` — fetch stock prices via yfinance
- `POST /debug/briefing` — generate AI market briefing
- `POST /debug/predictive` — compute predictive signals
- `GET  /debug/status` — table row counts for all major models

### Frontend Structure (`frontend/src/`)
- `app/` — Next.js App Router pages: `/`, `/industries/[slug]`, `/companies/[symbol]`, `/feed`, `/analyst`, `/graph`, `/admin`
- `app/use-*.ts` — React Query hooks co-located in `app/`: `use-analyst.ts`, `use-analytics.ts`, `use-graph.ts`, `use-market-data.ts`
- `components/layout/` — `app-sidebar.tsx` (main nav), `header.tsx`, theme provider/toggle
- `components/ui/` — shadcn/ui components
- `components/charts/` — ECharts + lightweight-charts wrappers
- `lib/api.ts` — `apiFetch<T>()` wrapper, base URL from `NEXT_PUBLIC_API_URL`
- `lib/constants.ts` — `INDUSTRY_COLORS`, `SENTIMENT_COLORS`, `SOURCE_LABELS`
- `stores/` — Zustand state
- `types/` — TypeScript types

### Database Schema (key relationships)
- `companies` ↔ `industries` — many-to-many via `company_industries`
- `raw_content` → `sentiment_scores` (one-to-one per company mention)
- `raw_content` → `entity_mentions` → `companies`
- `sentiment_scores` aggregated into `sentiment_aggregates` (hourly/daily per company or industry)
- `ai_briefings` link to company or industry; `anomaly_alerts` track z-score deviations
- `price_data` per company per date; `entity_relations` canonical-ordered company pairs
- `predictive_signal` — sentiment-price lead/lag signals

### Environment Variables
Copy `.env.example` to `.env` (backend) and `.env.local` (frontend). Key vars:
- `DATABASE_URL` — asyncpg connection string (default: localhost:5432)
- `REDIS_URL` — default: localhost:6379
- `ANTHROPIC_API_KEY` — Claude Haiku for LLM scoring
- `REDDIT_*` — asyncpraw credentials
- `TWITTER_*` — twikit credentials (username, email, password)
- `NEXT_PUBLIC_API_URL` — frontend API base (default: http://localhost:8000/api/v1)
- `NEXT_PUBLIC_SUPABASE_*` — Supabase keys (for production auth/realtime)
- `ENVIRONMENT` — set to `development` to enable debug endpoints

## Key Patterns

- **Async everywhere**: backend uses `asyncpg` + `async_session`, all route handlers must be `async def`
- **Dependency injection**: use `get_db()` and `get_cache()` from `dependencies.py` for DB/Redis access in routes
- **UUID primary keys**: all models inherit `UUIDMixin`; use `gen_random_uuid()` in PostgreSQL
- **Sentiment ensemble**: final score combines FinBERT (transformer) + Claude Haiku (LLM) outputs into `ensemble_score/label/confidence`
- **React Query**: frontend data fetching uses `@tanstack/react-query` v5 with custom hooks in `app/use-*.ts`; Zustand for UI state
- **Schemas separate from models**: Pydantic schemas in `app/schemas/` are distinct from SQLAlchemy models in `app/models/`
