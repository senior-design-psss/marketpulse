# MarketPulse AI

Real-time financial sentiment intelligence platform. Aggregates news, Reddit, and StockTwits data, scores it with a FinBERT + Claude Haiku AI ensemble, and presents it through a Bloomberg Terminal-inspired dashboard.

---

## Quick Start

```bash
# Backend
cd backend
pip install -e .
alembic upgrade head
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — then go to `/admin` and click **Run Full Pipeline**.

**Prerequisites:** PostgreSQL running locally, database `marketpulse` created.

---

## Architecture

```
[News RSS]  ──┐                                          ┌─ Industry Heatmap
[Reddit]    ──┼──► Ingestion ──► Text Cleaner ──► NLP ──►├─ Company Profiles
[StockTwits] ─┘    Pipeline      Entity Extractor  │     ├─ Live Feed
                                                   │     ├─ AI Analyst
                                         ┌─────────┴──┐  ├─ Entity Graph
                                         │FinBERT     │  └─ Watchlist + Prices
                                         │Claude Haiku│
                                         │(Ensemble)  │
                                         └─────┬──────┘
                                               │
                              ┌────────────────┼────────────────┐
                              ▼                ▼                ▼
                         [Postgres]      [Analytics]      [AI Analyst]
                         12 tables       Momentum         Briefings
                         Alembic         Anomalies        Summaries
                                         Confidence       Risk Alerts
                                         Predictive
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| **UI** | shadcn/ui, ECharts (heatmaps, radar, gauge, graph), TradingView Lightweight Charts |
| **State** | Zustand (client), TanStack Query (server) |
| **Backend** | FastAPI, Python 3.12, uvicorn |
| **NLP/ML** | ProsusAI/FinBERT (HuggingFace), spaCy NER |
| **LLM** | Claude Haiku 4.5 (Anthropic API) |
| **Ingestion** | News RSS (16 feeds), Reddit (public JSON), StockTwits (20 tickers) |
| **Database** | PostgreSQL, 12 tables, Alembic migrations |
| **Cache** | Redis (Upstash) |
| **Scheduling** | APScheduler (11 background jobs) |
| **Prices** | yfinance (Yahoo Finance) |

## Data Sources

| Source | Method | Items/Run | Key |
|--------|--------|-----------|-----|
| **News RSS** | 16 feeds (CNBC, Bloomberg, WSJ, MarketWatch, Seeking Alpha, etc.) | ~100-200 articles | None |
| **Reddit** | Public JSON endpoints (`r/wallstreetbets`, `r/stocks`, `r/investing`, etc.) | ~70-90 posts | None |
| **StockTwits** | Public API, 20 tracked tickers with pre-labeled bullish/bearish | ~400-500 messages | None |
| **Stock Prices** | yfinance daily OHLCV | 30 days × 38 stocks | None |

## API

30 REST endpoints under `/api/v1/` across 6 routers: industries, companies, sentiment, analytics, analyst, and graph. Full auto-generated docs available at `http://localhost:8000/docs` when the backend is running.

## Database Schema (12 tables)

| Table | Purpose |
|-------|---------|
| `industries` | 10 tracked sectors with display colors |
| `companies` | 40 tracked companies with aliases for entity matching |
| `company_industries` | Many-to-many sector mapping |
| `raw_content` | Ingested articles/posts from all sources |
| `entity_mentions` | NER-extracted company references per content item |
| `sentiment_scores` | FinBERT + LLM + ensemble scores per item |
| `sentiment_aggregates` | Hourly/daily rollups with per-source breakdown, momentum, confidence |
| `anomaly_alerts` | Z-score based sentiment spike detection |
| `ai_briefings` | AI-generated market reports and company summaries |
| `entity_relations` | Company co-mention counts and sentiment correlation |
| `price_data` | Daily OHLCV from yfinance |
| `predictive_signals` | Sentiment-price lead-lag correlations |

## Sentiment Engine

**Dual-model ensemble scoring:**

- **FinBERT** (ProsusAI/finbert) — 110M parameter BERT model fine-tuned on financial text. Returns positive/negative/neutral probabilities. Runs locally, free.
- **Claude Haiku 4.5** — Contextual LLM scoring on a -1.0 to +1.0 scale with reasoning. Understands sarcasm, complex narratives, multi-company articles.
- **Ensemble**: 70% LLM + 30% FinBERT weighted merge. Confidence based on model agreement. Graceful fallback to FinBERT-only when LLM unavailable.

**Entity extraction** uses word-boundary regex + financial context filtering to avoid false positives (e.g., "Apple" in "apple cider" won't match AAPL).

## Frontend Pages

| Page | Route | Features |
|------|-------|----------|
| **Dashboard** | `/` | Ticker tape, stats bar, industry heatmap, market gauge, watchlist with prices, news wire, AI briefing |
| **Industries** | `/industries` | Industry cards with sentiment scores |
| **Industry Detail** | `/industries/{slug}` | Radar chart (3 sources), company table |
| **Companies** | `/companies` | Full table: ticker, price, change%, sentiment, momentum, volume, confidence, signal |
| **Company Profile** | `/companies/{symbol}` | Price + sentiment header, 5 metric cards, price vs sentiment candlestick overlay, sentiment timeline, source donut, AI summary, source articles with scores |
| **Live Feed** | `/feed` | Filterable sentiment stream (source, label), pagination |
| **AI Analyst** | `/analyst` | Markdown briefing, risk alerts, predictive signals, briefing history |
| **Entity Graph** | `/graph` | Force-directed graph: industry hubs → company nodes, co-mention edges |
| **Control Panel** | `/admin` | Trigger all pipelines from UI, system status, activity log |

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql+asyncpg://marketpulse:localdev@localhost:5432/marketpulse

# Optional — enhances functionality
ANTHROPIC_API_KEY=sk-ant-...   # Enables LLM scoring + AI briefings
REDIS_URL=redis://localhost:6379  # Enables caching

# Not needed — all sources work without keys
# Reddit uses public JSON endpoints
# StockTwits uses public API
# News uses RSS feeds
```

## Background Jobs (11 scheduled)

| Job | Interval | Description |
|-----|----------|-------------|
| News Ingestion | 10 min | Scrape 16 RSS feeds |
| Reddit Ingestion | 15 min | Fetch from 7 subreddits |
| StockTwits Ingestion | 10 min | Poll 20 tickers |
| Sentiment Processing | 5 min | FinBERT + LLM scoring (batch of 50) |
| Analytics Pipeline | 15 min | Aggregates → momentum → confidence → anomalies |
| Daily Aggregates | 6 hours | Daily rollups |
| Price Fetch | 12 hours | yfinance OHLCV |
| AI Briefing | 6 hours | Claude Haiku market report |
| Entity Graph | 24 hours | Co-occurrence computation |
| Predictive Signals | 24 hours | Sentiment-price correlation |

---

## Final Design Report

### Team Members
- **Pratyush Srivastava**
- **Sid Shah**

### Advisor
- Prabhat Srivastava (VP Tech at Deutsche Bank)

### Project Abstract
MarketPulse AI is a real-time sentiment intelligence platform that aggregates financial news, Reddit discussions, and StockTwits posts. Using an ensemble of Claude Haiku LLM and FinBERT scoring, the system converts raw text streams into industry heatmaps, company trendlines, and AI-generated summaries. The platform features a Bloomberg Terminal-inspired interface built for clarity, speed, and insight consistency.

### User Stories

1. **As a retail investor**, I want to view real-time industry sentiment so that I can make informed decisions about my portfolio direction.
2. **As a market researcher**, I want comparable company trendlines so that I can analyze performance narratives across sectors.
3. **As a student learning finance**, I want sentiment explanations so that I understand why content is classified as positive or negative.
4. **As a dashboard user**, I want intuitive, color-coded visualizations so that I can understand market sentiment quickly.
5. **As a developer/maintainer**, I want structured endpoints and modular ingestion pipelines so that the system can be extended easily.

### Design Diagrams

- **Level 0 DFD** – Raw data flowing from external sources → sentiment engine → dashboard outputs.

![Diagram 0](app-docs/1.jpeg)

- **Level 1 DFD** – Separates ingestion pipelines, preprocessing, AI scoring, and dashboards.

![Diagram 1](app-docs/2.jpeg)

- **Level 2 DFD** – Details ingestion micro-modules, LLM classifier, FinBERT batcher, database storage, and REST API routes.

![Diagram 2](app-docs/3.jpeg)

### ABET Concerns

**Ethical:** We use only publicly available RSS, Reddit JSON, and StockTwits data. No user identities are collected. Sentiment scoring includes explainability to avoid misleading conclusions.

**Economic:** The project uses free-tier APIs, open-source NLP tools, and local-first development to keep costs minimal ($20 for LLM credits).

**Security:** Input sanitization, rate limiting, and database access rules reduce risks of data leaks, tampering, and pipeline overload.

**Social:** MarketPulse AI democratizes access to sentiment intelligence, benefiting students and entry-level researchers who lack access to professional trading tools.

### Budget

| Item | Cost |
|------|------|
| GitHub Student Pack | Free |
| Vercel Hosting | Free |
| Render Free Tier | Free |
| yfinance / RSS / Reddit / StockTwits | Free |
| Anthropic LLM Credits | $20 |

**Total Project Cost: $20**

### Professional Biographies

**Pratyush Srivastava** — Computer Science major specializing in AI engineering, automation, and scalable data systems. Experience includes multi-agent automation pipelines, ML-driven classification tools, and distributed ingestion architectures.

**Sid Shah** — Software engineering student with strong experience in backend engineering, ingestion pipelines, relational/analytical databases, and data-driven analytics infrastructure.

### Appendix

- **GitHub Repository:** https://github.com/senior-design-psss/marketpulse
- **Design Report PDF:** [app-docs/Report.pdf](app-docs/Report.pdf)

---

### Self-Assessment Essays

<details>
<summary>Pratyush Srivastava</summary>

Our senior design project, MarketPulse AI, is centered on building a real-time sentiment analysis platform that combines multi-source financial data ingestion, an ensemble AI scoring engine, and an interactive analytics dashboard. From my perspective as a Computer Science student deeply interested in AI systems, data engineering, and full-stack development, this project represents the perfect intersection of my academic strengths and professional goals. It allowed me to integrate concepts from machine learning, system design, and scalable web development into a unified, end-to-end solution.

My academic coursework has played a central role in guiding my approach to the technical challenges of this project. Subjects such as Data Structures, Algorithms, Machine Learning, Web Application Development, and Database Design helped me reason through architectural tradeoffs and build efficient components. These classes prepared me for implementing the backend services, integrating machine learning models, and designing the early stages of the frontend UX. Additionally, exposure to software engineering concepts such as modular design, version control workflows, and documentation standards has been crucial as we continue to build the system incrementally.

My professional experiences have also greatly influenced my contributions so far. Through my co-op roles in AI automation, full-stack engineering, and multi-agent pipeline development, I gained hands-on experience with ingestion systems, LLM-based classification, cloud deployment, and system reliability, skills that directly transfer to our ongoing work in MarketPulse AI. For example, my work at Acuvity with classification pipelines informed the design of our ensemble sentiment engine, while my automation experience at the SBDC helped shape my understanding of stable data ingestion and error-handling strategies. These experiences have allowed me to approach the project with a production-minded perspective, even at its current developmental stage.

One of my main motivations for choosing this project is its relevance to both my personal interests and long-term career goals. I have always been fascinated by financial markets and the role sentiment plays in shaping trends. Building a platform that synthesizes real-time signals from multiple sources and translates them into actionable insights is both challenging and exciting. Even though the system is not yet complete, the progress we have made has reinforced my enthusiasm for applied AI and large-scale systems engineering.

Our approach throughout the semester has been iterative. We began by finalizing our architecture, splitting responsibilities across ingestion, AI/NLP, backend API, and dashboard components. Up to this point, I have contributed primarily to developing the LLM sentiment classifier, integrating FinBERT, designing the ensemble scoring logic, and establishing the early version of the frontend dashboard. We have also completed early ingestion prototypes and integrated basic API routes. While several components, such as full real-time streaming, advanced charts, and complete data pipelines, are still in progress, our current milestones demonstrate steady, meaningful advancement. Looking ahead, I will continue refining the AI engine, expanding the dashboard features, and working toward a cohesive, end-to-end demo for the next phase. I will measure my success by how reliably the system operates, how seamlessly components integrate, and how effectively the final product communicates insights to its users.

</details>

<details>
<summary>Sid Shah</summary>

Our senior design project, MarketPulse AI, is focused on developing a real-time sentiment analysis platform that aggregates data from multiple financial sources and converts it into actionable insights through AI-driven scoring and interactive dashboards. While the project is still in development, we have made strong progress in building the ingestion infrastructure and defining a scalable architecture that supports future growth. As a Computer Science student with a strong interest in backend engineering and data-driven systems, this project has provided an ideal opportunity to apply and expand my technical skills in a meaningful, real-world context.

My academic coursework has played an important role in shaping how I approach the engineering challenges within this project. Classes such as Database Design, Algorithms, Data Structures, and Software Engineering have provided me with the foundational knowledge needed to build efficient ingestion pipelines and design a robust database schema for storing and querying sentiment data. These courses helped me reason about performance tradeoffs, normalization strategies, and system modularity, skills that have directly influenced the ingestion and backend components I've been developing. Additional coursework in distributed systems and data processing has strengthened my understanding of reliability and throughput, which are essential for large-scale data ingestion.

My previous project and work experiences have also been highly influential in guiding my contributions. Throughout past academic and personal projects involving web applications, APIs, and analytics pipelines, I gained practical experience with structuring backend routes, optimizing data flows, and building maintainable codebases. These experiences have helped me take ownership of the ingestion system and database layer within MarketPulse AI. I drew on this background to implement early versions of our Reddit and News ingestion modules, create data cleaning utilities, and design the relational schema that will feed into the sentiment engine and dashboard. The opportunity to integrate these skills into a collaborative capstone project has been both challenging and rewarding.

My motivation for choosing this project stems from my interest in data engineering and backend development. I enjoy working on systems that transform raw information into structured, meaningful insights, and MarketPulse AI aligns perfectly with that interest. The idea of building real-time ingestion pipelines, ensuring data reliability, and supporting an AI-driven analytics engine closely aligns with the type of work I hope to pursue in the future. Even though the system is still incomplete, the progress we've made has strengthened my confidence in designing scalable backend components and collaborating effectively within a team.

Throughout the semester, our team has followed an iterative approach, gradually building each subsystem while refining requirements along the way. My contributions so far include implementing ingestion scripts for Reddit and News RSS feeds, designing the initial preprocessing pipeline, creating the database schema, and laying the groundwork for analytical query support. I have also worked on coordinating our task timeline and ensuring alignment between ingestion outputs and API needs. Looking ahead, I plan to continue expanding the ingestion layer, finalize our data storage logic, and support the integration of our backend with the frontend and AI engine. I will measure my progress by the reliability, accuracy, and performance of the ingestion and database systems, as well as how seamlessly they integrate with the remaining components as we move toward our final demo.

</details>
