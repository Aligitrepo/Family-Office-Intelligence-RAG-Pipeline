"""
demo.py
=======
Headless demo runner — executes 5 pre-validated queries against the live RAG
pipeline and saves formatted results to docs/demo_output.md.

Run after ingest:
    python -m backend.demo
"""

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / "docs" / "demo_output.md"

# ── Demo queries — verified against the actual dataset ────────────────────
DEMO_QUERIES = [
    {
        "id": 1,
        "category": "Sector / Geography",
        "query": "Which family offices in Europe focus on luxury or consumer goods investments?",
        "filters": {},
        "k": 8,
        "expected_ids": ["FO-0013", "FO-0004", "FO-0003"],  # Arnault, GBL, CNP
    },
    {
        "id": 2,
        "category": "AUM Ranking",
        "query": "What are the largest single-family offices in the dataset by AUM?",
        "filters": {"fo_type": "SFO"},
        "k": 10,
        "expected_ids": ["FO-0013", "FO-0057", "FO-0054", "FO-0074"],  # Arnault, Gates, Bezos, Soros
    },
    {
        "id": 3,
        "category": "US / Regulatory",
        "query": "Which US family offices are SEC-registered investment advisers with known decision makers?",
        "filters": {"hq_country": "United States", "has_dm": True},
        "k": 8,
        "expected_ids": ["FO-0057", "FO-0082", "FO-0065", "FO-0074"],  # Cascade, Willett, MSD, Soros
    },
    {
        "id": 4,
        "category": "Asia-Pacific",
        "query": "Tell me about family offices in India and Asia and their investment strategies",
        "filters": {},
        "k": 8,
        "expected_ids": ["FO-0021", "FO-0034", "FO-0048"],  # Premji, Dymon, Hinduja
    },
    {
        "id": 5,
        "category": "Deal Size / Check",
        "query": "Which family offices have disclosed check sizes above $100M and what sectors do they target?",
        "filters": {"has_check_size": True},
        "k": 10,
        "expected_ids": ["FO-0057", "FO-0018", "FO-0037", "FO-0074"],  # Cascade, CK Asset, Investor AB, Soros
    },
]


def format_aum(val):
    if not val or float(val) < 0:
        return "N/A"
    v = float(val)
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}T"
    if v >= 1000:
        return f"${v/1000:.0f}B"
    return f"${v:.0f}M"


def run():
    from backend.pipeline import QueryFilters, RAGPipeline

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log.error("OPENAI_API_KEY not set.")
        sys.exit(1)

    log.info("Initialising RAG pipeline...")
    try:
        pipeline = RAGPipeline()
    except RuntimeError as e:
        log.error("%s", e)
        sys.exit(1)

    lines = []
    lines.append("# Family Office Intelligence — RAG Demo Output")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ")
    lines.append("**Dataset:** 238 validated family office records (Task 1)  ")
    lines.append("**Pipeline:** ChromaDB + OpenAI text-embedding-3-small + GPT-4o-mini  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    for dq in DEMO_QUERIES:
        log.info("Running query %d/%d: %s", dq["id"], len(DEMO_QUERIES), dq["query"][:60])

        fdict = dq.get("filters", {})
        filters = QueryFilters(
            fo_type=fdict.get("fo_type"),
            hq_country=fdict.get("hq_country"),
            min_aum_usd_m=fdict.get("min_aum_usd_m"),
            max_aum_usd_m=fdict.get("max_aum_usd_m"),
            has_check_size=fdict.get("has_check_size"),
            has_strategy=fdict.get("has_strategy"),
            has_aum=fdict.get("has_aum"),
            has_dm=fdict.get("has_dm"),
            confidence_score=fdict.get("confidence_score"),
        )

        result = pipeline.query(text=dq["query"], filters=filters, k=dq["k"])

        lines.append(f"## Query {dq['id']} — {dq['category']}")
        lines.append("")
        lines.append(f"> **{dq['query']}**")
        lines.append("")

        if fdict:
            lines.append(f"*Filters applied: `{fdict}`*  ")
            lines.append(f"*Retrieve top-{dq['k']} records*")
            lines.append("")

        lines.append("### Answer")
        lines.append("")
        lines.append(result.answer)
        lines.append("")

        # Check expected IDs present
        retrieved_ids = {r.fo_id for r in result.records}
        hit_ids = [eid for eid in dq["expected_ids"] if eid in retrieved_ids]
        lines.append(f"*Retrieval check: {len(hit_ids)}/{len(dq['expected_ids'])} expected records retrieved*")
        lines.append("")

        lines.append("### Retrieved Source Records")
        lines.append("")
        lines.append("| Rank | FO ID | Name | Type | Country | AUM | Confidence | Distance |")
        lines.append("|------|-------|------|------|---------|-----|-----------|----------|")
        for i, r in enumerate(result.records, 1):
            lines.append(
                f"| {i} | {r.fo_id} | {r.fo_name[:40]} | {r.fo_type} "
                f"| {r.hq_country} | {format_aum(r.aum_usd_m)} "
                f"| {r.confidence_score} | {r.distance} |"
            )
        lines.append("")
        lines.append(f"*Model: {result.model_used} · Retrieved: {result.retrieval_count} records*")
        lines.append("")
        lines.append("---")
        lines.append("")

    output = "\n".join(lines)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(output, encoding="utf-8")
    log.info("Demo output saved to %s", OUTPUT_FILE)
    print(f"\nDemo complete. Output written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    run()
