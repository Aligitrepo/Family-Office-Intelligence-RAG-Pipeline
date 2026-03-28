"""
pipeline.py
===========
RAGPipeline: hybrid retrieval + generation over the family office dataset.

Retrieval approach:
  1. Optional metadata pre-filter (fo_type, hq_country, aum_usd_m, check_size)
  2. Semantic cosine-similarity search in ChromaDB (k configurable)
  3. GPT-4o-mini generation with strict grounding prompt
  4. Response cites source FO IDs and names; never invents information
"""

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", ROOT / "data" / "chroma_db"))
COLLECTION_NAME = "family_offices"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """\
You are a family office intelligence analyst with access to a validated dataset of \
238 family offices worldwide. Your answers must be:

1. GROUNDED: Only use information present in the retrieved context below. Do not \
   add external knowledge or make assumptions beyond what is explicitly stated.
2. CITED: Every family office you mention must include its FO ID in parentheses, \
   e.g. "Groupe Arnault (FO-0013)".
3. HONEST: If the context does not contain enough information to answer the query \
   fully, say so explicitly. Do not fabricate details.
4. STRUCTURED: Use bullet points or a numbered list when listing multiple entities. \
   End with a brief "Sources" section listing all FO IDs used.

If no relevant records are found, say: "No matching family offices found in the \
dataset for this query."
"""


@dataclass
class QueryFilters:
    """Optional metadata filters for pre-filtering the ChromaDB collection."""
    fo_type: Optional[str] = None          # "SFO" | "MFO" | "VFO"
    hq_country: Optional[str] = None       # exact country string
    min_aum_usd_m: Optional[float] = None  # minimum AUM in USD millions
    max_aum_usd_m: Optional[float] = None  # maximum AUM in USD millions
    has_check_size: Optional[bool] = None  # True = only records with check size data
    has_strategy: Optional[bool] = None    # True = only records with strategy data
    has_aum: Optional[bool] = None         # True = only records with AUM data
    has_dm: Optional[bool] = None          # True = only records with a named decision maker
    confidence_score: Optional[str] = None # "H" | "M"


@dataclass
class RetrievedRecord:
    fo_id: str
    fo_name: str
    fo_type: str
    hq_country: str
    hq_city: str
    aum_usd_m: float
    confidence_score: str
    document: str
    distance: float
    metadata: dict = field(default_factory=dict)


@dataclass
class RAGResponse:
    query: str
    answer: str
    records: list[RetrievedRecord]
    model_used: str
    retrieval_count: int
    filters_applied: dict


class RAGPipeline:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set in environment.")

        self.openai = OpenAI(api_key=api_key)
        self.chroma = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))

        try:
            self.collection = self.chroma.get_collection(COLLECTION_NAME)
            log.info(
                "Connected to ChromaDB collection '%s' (%d documents)",
                COLLECTION_NAME,
                self.collection.count(),
            )
        except Exception:
            raise RuntimeError(
                f"ChromaDB collection '{COLLECTION_NAME}' not found. "
                "Run backend/ingest.py first."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(
        self,
        text: str,
        filters: Optional[QueryFilters] = None,
        k: int = 8,
    ) -> RAGResponse:
        """Answer a natural language query using hybrid retrieval + generation."""
        filters = filters or QueryFilters()

        # 1. Auto-infer any missing filters from query intent
        self._infer_filters_from_query(text, filters)

        # 2. Embed the query
        query_embedding = self._embed(text)

        # 3. Build ChromaDB where-clause from filters
        where = self._build_where(filters)
        filters_applied = {k: v for k, v in (where or {}).items()}

        # 4. Semantic search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self.collection.count()),
            where=where if where else None,
            include=["documents", "metadatas", "distances"],
        )

        records = self._parse_results(results)

        # 5. Generate grounded answer
        answer = self._generate(text, records)

        return RAGResponse(
            query=text,
            answer=answer,
            records=records,
            model_used=CHAT_MODEL,
            retrieval_count=len(records),
            filters_applied=filters_applied,
        )

    def stats(self) -> dict:
        """Return dataset statistics for the frontend stats panel."""
        count = self.collection.count()
        # Retrieve all metadata for statistics
        all_results = self.collection.get(include=["metadatas"])
        metas = all_results.get("metadatas", [])

        from collections import Counter
        type_counts = Counter(m.get("fo_type", "Unknown") for m in metas)
        country_counts = Counter(m.get("hq_country", "") for m in metas)
        conf_counts = Counter(m.get("confidence_score", "") for m in metas)

        return {
            "total_records": count,
            "fo_types": dict(type_counts),
            "top_countries": dict(country_counts.most_common(10)),
            "confidence": dict(conf_counts),
            "with_aum": sum(1 for m in metas if m.get("has_aum")),
            "with_decision_maker": sum(1 for m in metas if m.get("has_dm")),
            "with_strategy": sum(1 for m in metas if m.get("has_strategy")),
            "with_check_size": sum(1 for m in metas if m.get("has_check_size")),
            "embedding_model": EMBEDDING_MODEL,
            "chat_model": CHAT_MODEL,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _embed(self, text: str) -> list[float]:
        response = self.openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    def _build_where(self, f: QueryFilters) -> Optional[dict]:
        """Translate QueryFilters into a ChromaDB $and where clause."""
        conditions = []

        if f.fo_type:
            conditions.append({"fo_type": {"$eq": f.fo_type}})
        if f.hq_country:
            conditions.append({"hq_country": {"$eq": f.hq_country}})
        if f.min_aum_usd_m is not None:
            conditions.append({"aum_usd_m": {"$gte": f.min_aum_usd_m}})
        if f.max_aum_usd_m is not None:
            conditions.append({"aum_usd_m": {"$lte": f.max_aum_usd_m}})
        if f.has_check_size is not None:
            conditions.append({"has_check_size": {"$eq": f.has_check_size}})
        if f.has_strategy is not None:
            conditions.append({"has_strategy": {"$eq": f.has_strategy}})
        if f.has_aum is not None:
            conditions.append({"has_aum": {"$eq": f.has_aum}})
        if f.has_dm is not None:
            conditions.append({"has_dm": {"$eq": f.has_dm}})
        if f.confidence_score:
            conditions.append({"confidence_score": {"$eq": f.confidence_score}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def _infer_filters_from_query(self, text: str, filters: QueryFilters) -> None:
        """
        Auto-infer metadata filters from query intent to improve retrieval quality.
        Only sets a filter if it has not already been explicitly provided by the caller.
        Mutates `filters` in place.
        """
        t = text.lower()

        # ── FO type ──────────────────────────────────────────────────────────
        if filters.fo_type is None:
            if re.search(r'\bsingle[- ]family\b|\bsfo\b', t):
                filters.fo_type = "SFO"
                log.info("Query intent: inferred fo_type=SFO")
            elif re.search(r'\bmulti[- ]family\b|\bmfo\b', t):
                filters.fo_type = "MFO"
                log.info("Query intent: inferred fo_type=MFO")

        # ── AUM ranking ───────────────────────────────────────────────────────
        # "largest/biggest/by AUM/wealthiest" → only retrieve records with AUM data
        # otherwise thin records with no AUM surface and the LLM cannot answer
        if filters.has_aum is None:
            if re.search(
                r'\blargest\b|\bbiggest\b|\bby aum\b|\bmost aum\b|\bhighest aum\b'
                r'|\baum rank\b|\bwealthiest\b|\brichest\b|\brank.*aum\b',
                t,
            ):
                filters.has_aum = True
                log.info("Query intent: inferred has_aum=True (AUM-ranking query)")

        # ── Decision makers ───────────────────────────────────────────────────
        # "decision maker/known DM/who runs/key person/principals" →
        # only retrieve records that have a named decision maker stored
        if filters.has_dm is None:
            if re.search(
                r'\bdecision[- ]maker\b|\bdecision maker\b|\bknown.*decision\b'
                r'|\bwho run\b|\bwho manage\b|\bwho lead\b|\bwho head\b'
                r'|\bkey person\b|\bkey contact\b|\bprincipals?\b'
                r'|\bnamed.*person\b|\bnamed.*contact\b',
                t,
            ):
                filters.has_dm = True
                log.info("Query intent: inferred has_dm=True (decision-maker query)")

        # ── Check size ────────────────────────────────────────────────────────
        if filters.has_check_size is None:
            if re.search(r'\bcheck size\b|\bticket size\b|\binvestment size\b|\bcheck sizes\b', t):
                filters.has_check_size = True
                log.info("Query intent: inferred has_check_size=True")

        # ── Investment strategy / sector focus ────────────────────────────────
        # Match "strateg*" (strategy/strategies/strategic), "sector focus",
        # "asset class", "portfolio", and common phrasings
        if filters.has_strategy is None:
            if re.search(
                r'\bstrateg\w+\b|\bsector focus\b|\basset class\b'
                r'|\btheir investment\b|\bhow.*invest\b|\bwhat.*invest\b'
                r'|\bportfolio\b|\binvest in\b',
                t,
            ):
                filters.has_strategy = True
                log.info("Query intent: inferred has_strategy=True")

        # ── Country: United States ────────────────────────────────────────────
        # Detect US-specific queries (but NOT when combined with broader regions
        # like "Europe and the US" or "global" which would make the filter wrong)
        if filters.hq_country is None:
            is_us_query = re.search(
                r'\bin the us\b|\bus family\b|\bus-based\b|\bunited states\b'
                r'|\bamerican family\b|\bsec.register\b|\bregistered investment adviser\b'
                r'\bsec registered\b',
                t,
            )
            has_other_region = re.search(
                r'\beurope\b|\basia\b|\bindia\b|\buk\b|\bglobal\b|\binternational\b'
                r'|\bworldwide\b|\baround the world\b',
                t,
            )
            if is_us_query and not has_other_region:
                filters.hq_country = "United States"
                log.info("Query intent: inferred hq_country=United States")

    def _parse_results(self, results: dict) -> list[RetrievedRecord]:
        records = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for fo_id, doc, meta, dist in zip(ids, docs, metas, distances):
            records.append(
                RetrievedRecord(
                    fo_id=fo_id,
                    fo_name=meta.get("fo_name", ""),
                    fo_type=meta.get("fo_type", ""),
                    hq_country=meta.get("hq_country", ""),
                    hq_city=meta.get("hq_city", ""),
                    aum_usd_m=meta.get("aum_usd_m", -1.0),
                    confidence_score=meta.get("confidence_score", ""),
                    document=doc,
                    distance=round(dist, 4),
                    metadata=meta,
                )
            )
        return records

    def _generate(self, query: str, records: list[RetrievedRecord]) -> str:
        if not records:
            return "No matching family offices found in the dataset for this query."

        context_parts = []
        for r in records:
            context_parts.append(f"[{r.fo_id}] {r.document}")
        context = "\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Context (retrieved family office records):\n\n{context}\n\n"
                    f"Query: {query}"
                ),
            },
        ]

        response = self.openai.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()
