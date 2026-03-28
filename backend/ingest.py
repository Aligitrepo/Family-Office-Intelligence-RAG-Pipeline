"""
ingest.py
=========
One-time ingestion script for the Task 1 family office dataset.

Steps:
  1. Read family_office_dataset.csv
  2. Synthesize a natural language document for each record
  3. Embed each document with OpenAI text-embedding-3-small
  4. Store in ChromaDB with rich metadata for hybrid filtering

Run once before starting the API:
    python backend/ingest.py
"""

import csv
import json
import logging
import os
import sys
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
DATASET_CSV = Path(os.getenv("DATASET_CSV_PATH", ROOT.parent / "task1" / "data" / "output" / "family_office_dataset.csv"))
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", ROOT / "data" / "chroma_db"))
COLLECTION_NAME = "family_offices"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBED_BATCH_SIZE = 50


def na(val: str) -> bool:
    return not val or val.strip().upper() in ("N/A", "NONE", "")


def synthesize_document(r: dict) -> str:
    """Convert a CSV row into a rich natural language document for embedding.

    Design rationale: embedding models are trained on natural language, not
    key=value pairs. Synthesizing prose dramatically improves retrieval
    relevance compared to embedding raw CSV rows.
    """
    parts = []

    # Identity line — always present
    fo_type_label = {
        "SFO": "Single Family Office (SFO)",
        "MFO": "Multi-Family Office (MFO)",
        "VFO": "Virtual Family Office (VFO)",
    }.get(r.get("fo_type", "").strip(), r.get("fo_type", "Family Office"))

    city = r.get("hq_city", "").strip()
    country = r.get("hq_country", "").strip()
    location = ", ".join(p for p in [city, country] if p)

    parts.append(
        f"{r['fo_name']} is a {fo_type_label} headquartered in {location}."
    )

    # Founding
    ff = r.get("founding_family", "")
    fy = r.get("founding_year", "")
    if not na(ff) and not na(fy):
        parts.append(f"Founding family: {ff} (established {fy}).")
    elif not na(ff):
        parts.append(f"Founding family: {ff}.")
    elif not na(fy):
        parts.append(f"Founded in {fy}.")

    # AUM
    aum = r.get("aum_estimate_usd_m", "")
    aum_src = r.get("aum_source", "")
    aum_range = r.get("aum_range", "")
    if not na(aum):
        aum_str = f"~${int(float(aum)):,}M"
        src_note = f" (source: {aum_src})" if not na(aum_src) else ""
        parts.append(f"Assets under management: {aum_str}{src_note}.")
    elif not na(aum_range):
        parts.append(f"AUM range: {aum_range}.")

    # Registration
    reg = r.get("registration_status", "")
    crd = r.get("crd_number", "")
    if not na(reg):
        crd_note = f" (CRD: {crd})" if not na(crd) else ""
        parts.append(f"Registration: {reg}{crd_note}.")

    # Investment profile
    strategy = r.get("investment_strategy", "")
    asset_class = r.get("asset_class_focus", "")
    sector = r.get("sector_focus", "")
    geo = r.get("geographic_focus", "")
    if not na(strategy):
        parts.append(f"Investment strategy: {strategy}.")
    if not na(asset_class):
        parts.append(f"Asset class focus: {asset_class}.")
    if not na(sector):
        parts.append(f"Sector focus: {sector}.")
    if not na(geo):
        parts.append(f"Geographic focus: {geo}.")

    # Check size
    cs_min = r.get("check_size_min_usd_m", "")
    cs_max = r.get("check_size_max_usd_m", "")
    if not na(cs_min) and not na(cs_max):
        parts.append(f"Typical check size: ${cs_min}M–${cs_max}M.")
    elif not na(cs_min):
        parts.append(f"Minimum check size: ${cs_min}M.")

    # Co-investment
    co_inv = r.get("co_invest_frequency", "")
    if not na(co_inv):
        parts.append(f"Co-investment frequency: {co_inv}.")

    # Impact/ESG
    esg = r.get("impact_esg_focus", "")
    if not na(esg):
        parts.append(f"Impact/ESG focus: {esg}.")

    # Decision makers
    dms = []
    for i in range(1, 4):
        name = r.get(f"dm{i}_name", "")
        title = r.get(f"dm{i}_title", "")
        if not na(name):
            dm_str = name
            if not na(title):
                dm_str += f" ({title})"
            dms.append(dm_str)
    if dms:
        parts.append(f"Key decision makers: {'; '.join(dms)}.")

    # Website
    website = r.get("website", "")
    if not na(website):
        parts.append(f"Website: {website}.")

    # Classification
    conf = r.get("confidence_score", "")
    vstatus = r.get("validation_status", "")
    evidence = r.get("fo_classification_evidence", "")
    if not na(vstatus) and not na(conf):
        conf_label = {"H": "High confidence", "M": "Medium confidence"}.get(conf, conf)
        parts.append(f"Classification: {vstatus} / {conf_label}.")
    if not na(evidence):
        parts.append(f"Evidence: {evidence}")

    return " ".join(parts)


def build_metadata(r: dict) -> dict:
    """Extract structured metadata for ChromaDB metadata filtering.

    Only scalar types (str, int, float, bool) are allowed by ChromaDB.
    """
    aum_val = None
    raw_aum = r.get("aum_estimate_usd_m", "")
    if not na(raw_aum):
        try:
            aum_val = float(raw_aum)
        except ValueError:
            pass

    cs_min = None
    raw_cs = r.get("check_size_min_usd_m", "")
    if not na(raw_cs):
        try:
            cs_min = float(raw_cs)
        except ValueError:
            pass

    return {
        "fo_id": r.get("fo_id", ""),
        "fo_name": r.get("fo_name", ""),
        "fo_type": r.get("fo_type", "Unknown"),
        "hq_country": r.get("hq_country", ""),
        "hq_city": r.get("hq_city", ""),
        "aum_usd_m": aum_val if aum_val is not None else -1.0,
        "aum_range": r.get("aum_range", "Unknown"),
        "check_size_min_usd_m": cs_min if cs_min is not None else -1.0,
        "confidence_score": r.get("confidence_score", ""),
        "has_aum": aum_val is not None,
        "has_dm": not na(r.get("dm1_name", "")),
        "has_strategy": not na(r.get("investment_strategy", "")),
        "has_check_size": cs_min is not None,
        "investment_strategy": r.get("investment_strategy", ""),
        "sector_focus": r.get("sector_focus", ""),
        "geographic_focus": r.get("geographic_focus", ""),
        "registration_status": r.get("registration_status", ""),
        "founding_family": r.get("founding_family", ""),
        "website": r.get("website", ""),
        "source_primary": r.get("source_primary", ""),
    }


def get_embeddings(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Batch-embed texts using OpenAI embeddings API."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def run():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log.error("OPENAI_API_KEY not set. Create a .env file from .env.example.")
        sys.exit(1)

    if not DATASET_CSV.exists():
        log.error("Dataset CSV not found at %s", DATASET_CSV)
        sys.exit(1)

    log.info("Loading dataset from %s", DATASET_CSV)
    with open(DATASET_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    log.info("Loaded %d records", len(rows))

    # Synthesize documents
    log.info("Synthesizing natural language documents...")
    documents = [synthesize_document(r) for r in rows]
    ids = [r["fo_id"] for r in rows]
    metadatas = [build_metadata(r) for r in rows]

    log.info("Sample document (FO-0013):")
    idx = next((i for i, r in enumerate(rows) if r.get("fo_id") == "FO-0013"), 0)
    log.info("\n%s", documents[idx])

    # Connect to ChromaDB
    log.info("Connecting to ChromaDB at %s", CHROMA_DB_PATH)
    CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
    chroma = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))

    # Drop and recreate collection for clean ingest
    existing = [c.name for c in chroma.list_collections()]
    if COLLECTION_NAME in existing:
        log.info("Dropping existing collection '%s'", COLLECTION_NAME)
        chroma.delete_collection(COLLECTION_NAME)

    collection = chroma.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    log.info("Created collection '%s'", COLLECTION_NAME)

    # Embed and upsert in batches
    openai_client = OpenAI(api_key=api_key)
    total = len(documents)
    log.info("Embedding %d documents in batches of %d...", total, EMBED_BATCH_SIZE)

    for start in tqdm(range(0, total, EMBED_BATCH_SIZE), desc="Embedding"):
        end = min(start + EMBED_BATCH_SIZE, total)
        batch_docs = documents[start:end]
        batch_ids = ids[start:end]
        batch_meta = metadatas[start:end]

        embeddings = get_embeddings(openai_client, batch_docs)

        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=batch_meta,
        )

    final_count = collection.count()
    log.info("Ingestion complete. %d documents stored in ChromaDB.", final_count)

    # Save ingestion manifest
    manifest = {
        "records_ingested": final_count,
        "embedding_model": EMBEDDING_MODEL,
        "collection": COLLECTION_NAME,
        "chroma_db_path": str(CHROMA_DB_PATH),
        "dataset_csv": str(DATASET_CSV),
    }
    manifest_path = CHROMA_DB_PATH / "ingest_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    log.info("Manifest saved to %s", manifest_path)


if __name__ == "__main__":
    run()
