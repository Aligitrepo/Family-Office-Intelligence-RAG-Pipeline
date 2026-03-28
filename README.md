# Task 2 — Family Office Intelligence RAG Pipeline

A full-stack RAG (Retrieval-Augmented Generation) application that makes the 238-record
Task 1 family office dataset queryable via natural language.

## Architecture

```
task2/
├── backend/
│   ├── ingest.py       One-time ingestion: CSV → ChromaDB
│   ├── pipeline.py     RAGPipeline class (hybrid retrieval + generation)
│   ├── main.py         FastAPI REST API
│   └── demo.py         Headless demo runner (5 queries → demo_output.md)
├── frontend/
│   └── src/
│       ├── App.jsx             Main layout (3-column: filters | query+results | stats)
│       ├── api.js              API client
│       └── components/
│           ├── StatsPanel.jsx  Dataset statistics sidebar
│           ├── FilterPanel.jsx Metadata filter controls
│           └── ResultCard.jsx  Expandable source record card
├── data/
│   └── chroma_db/      ChromaDB persistent store (git-ignored)
└── docs/
    ├── rag_methodology.md   Full methodology document
    └── demo_output.md       Generated demo query output
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key

### Backend

```bash
cd task2

# Install dependencies
pip install -r backend/requirements.txt

# Create .env from template
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run one-time ingestion (embeds 238 records into ChromaDB)
python -m backend.ingest

# Start the FastAPI server
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd task2/frontend

npm install
npm run dev
# Open http://localhost:5173
```

### Run demo queries (no frontend required)

```bash
cd task2
python -m backend.demo
# Output saved to docs/demo_output.md
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/query` | Natural language query → grounded answer + citations |
| `GET` | `/api/stats` | Dataset statistics |
| `GET` | `/api/examples` | Pre-validated example queries |
| `GET` | `/api/health` | Liveness check |
| `GET` | `/docs` | FastAPI interactive documentation |

### Example query request

```json
POST /api/query
{
  "query": "Which European family offices focus on luxury consumer goods?",
  "fo_type": "SFO",
  "k": 8
}
```

### Example filters

```json
{
  "fo_type": "SFO",
  "hq_country": "United States",
  "min_aum_usd_m": 10000,
  "has_strategy": true,
  "confidence_score": "H",
  "k": 10
}
```

## Stack

- **Vector DB**: ChromaDB (local persistent, HNSW cosine similarity)
- **Embeddings**: OpenAI `text-embedding-3-small` (1536 dims)
- **LLM**: OpenAI `gpt-4o-mini` (grounded, cited responses)
- **Backend**: FastAPI + Uvicorn
- **Frontend**: React 18 + Vite

See `docs/rag_methodology.md` for full architecture decisions, chunking strategy,
limitations, and improvement roadmap.
