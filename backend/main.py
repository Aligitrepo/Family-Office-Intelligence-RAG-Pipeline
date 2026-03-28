"""
main.py
=======
FastAPI application — REST backend for the family office RAG pipeline.

Endpoints:
  POST /api/query        Natural language query → grounded answer + citations
  GET  /api/stats        Dataset and pipeline statistics
  GET  /api/health       Liveness check
  GET  /api/examples     Pre-validated example queries for the UI

Run:
    uvicorn backend.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.pipeline import QueryFilters, RAGPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Global pipeline instance ────────────────────────────────────────────────
pipeline: RAGPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    log.info("Initialising RAG pipeline...")
    try:
        pipeline = RAGPipeline()
        log.info("RAG pipeline ready.")
    except RuntimeError as e:
        log.error("Failed to initialise pipeline: %s", e)
        log.error("Have you run `python -m backend.ingest` yet?")
        pipeline = None
    yield
    log.info("Shutting down.")


app = FastAPI(
    title="Family Office Intelligence API",
    description=(
        "RAG pipeline over the PolarityIQ Task 1 family office dataset. "
        "238 validated records, 56 fields, 25 countries."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language query")
    k: int = Field(8, ge=1, le=20, description="Number of documents to retrieve")
    fo_type: Optional[str] = Field(None, description="Filter by type: SFO | MFO | VFO")
    hq_country: Optional[str] = Field(None, description="Filter by country (exact match)")
    min_aum_usd_m: Optional[float] = Field(None, ge=0, description="Minimum AUM in USD millions")
    max_aum_usd_m: Optional[float] = Field(None, ge=0, description="Maximum AUM in USD millions")
    has_check_size: Optional[bool] = Field(None, description="Only return records with check size data")
    has_strategy: Optional[bool] = Field(None, description="Only return records with strategy data")
    has_aum: Optional[bool] = Field(None, description="Only return records with AUM data")
    has_dm: Optional[bool] = Field(None, description="Only return records with a named decision maker")
    confidence_score: Optional[str] = Field(None, description="Filter by confidence: H | M")


class RecordSnippet(BaseModel):
    fo_id: str
    fo_name: str
    fo_type: str
    hq_country: str
    hq_city: str
    aum_usd_m: float
    confidence_score: str
    distance: float
    metadata: dict


class QueryResponse(BaseModel):
    query: str
    answer: str
    records: list[RecordSnippet]
    model_used: str
    retrieval_count: int
    filters_applied: dict


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok" if pipeline is not None else "degraded",
        "pipeline_ready": pipeline is not None,
        "message": "RAG pipeline ready" if pipeline else "Run ingest.py first",
    }


@app.get("/api/stats")
def stats():
    if pipeline is None:
        raise HTTPException(503, "Pipeline not ready. Run backend/ingest.py first.")
    return pipeline.stats()


@app.get("/api/examples")
def examples():
    """Return pre-validated example queries for the frontend UI."""
    return {
        "examples": [
            {
                "id": 1,
                "query": "Which family offices in Europe focus on luxury or consumer goods?",
                "category": "Sector Focus",
                "hint": "Tests semantic retrieval on sector_focus field",
                "filters": {},
            },
            {
                "id": 2,
                "query": "What are the largest single-family offices in the dataset by AUM?",
                "category": "AUM Ranking",
                "hint": "Tests numerical reasoning over aum_estimate_usd_m",
                "filters": {"fo_type": "SFO"},
            },
            {
                "id": 3,
                "query": "Which US family offices are SEC-registered and have known decision makers?",
                "category": "US / Regulatory",
                "hint": "Tests metadata filtering on hq_country + has_dm",
                "filters": {"hq_country": "United States"},
            },
            {
                "id": 4,
                "query": "Tell me about family offices in India and their investment strategies",
                "category": "Asia-Pacific",
                "hint": "Tests geographic + strategy retrieval",
                "filters": {},
            },
            {
                "id": 5,
                "query": "Which family offices have check sizes above $100M and what sectors do they target?",
                "category": "Deal Size",
                "hint": "Tests check_size metadata + sector_focus retrieval",
                "filters": {"has_check_size": True},
            },
        ]
    }


@app.post("/api/query", response_model=QueryResponse)
def query_pipeline(req: QueryRequest):
    if pipeline is None:
        raise HTTPException(503, "Pipeline not ready. Run backend/ingest.py first.")

    filters = QueryFilters(
        fo_type=req.fo_type,
        hq_country=req.hq_country,
        min_aum_usd_m=req.min_aum_usd_m,
        max_aum_usd_m=req.max_aum_usd_m,
        has_check_size=req.has_check_size,
        has_strategy=req.has_strategy,
        has_aum=req.has_aum,
        has_dm=req.has_dm,
        confidence_score=req.confidence_score,
    )

    try:
        result = pipeline.query(text=req.query, filters=filters, k=req.k)
    except Exception as e:
        log.exception("Query failed: %s", e)
        raise HTTPException(500, f"Query failed: {str(e)}")

    return QueryResponse(
        query=result.query,
        answer=result.answer,
        records=[
            RecordSnippet(
                fo_id=r.fo_id,
                fo_name=r.fo_name,
                fo_type=r.fo_type,
                hq_country=r.hq_country,
                hq_city=r.hq_city,
                aum_usd_m=r.aum_usd_m,
                confidence_score=r.confidence_score,
                distance=r.distance,
                metadata=r.metadata,
            )
            for r in result.records
        ],
        model_used=result.model_used,
        retrieval_count=result.retrieval_count,
        filters_applied=result.filters_applied,
    )
