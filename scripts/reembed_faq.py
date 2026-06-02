"""
Re-embed all faq_items in Supabase using bge-m3:latest
- Fetches records in pages directly from DB
- Uses UPDATE (not insert) to avoid duplicates
- Batches embed calls for speed
"""
import os, sys, time, math, requests
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
EMBED_MODEL  = os.getenv("EMBED_MODEL", "bge-m3:latest")
EMBED_DIM    = int(os.getenv("EMBED_DIMENSION", "1024"))
BATCH_SIZE   = 1   # bge-m3 struggles with large batch+long text
PAGE_SIZE    = 200
CHUNK_SIZE   = 150 # chars per chunk for NaN-fallback chunk-averaging

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def embed_batch(texts: list[str]) -> list[list[float]]:
    r = requests.post(f"{EMBED_URL}/api/embed",
                      json={"model": EMBED_MODEL, "input": texts},
                      timeout=120)
    r.raise_for_status()
    return r.json()["embeddings"]


def valid(vec) -> bool:
    return (vec and len(vec) == EMBED_DIM and
            not any(v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))
                    for v in vec))


def embed_with_fallback(text: str) -> list[float] | None:
    """Try full-text embed; on NaN fall back to chunk-averaging."""
    try:
        vecs = embed_batch([text])
        if valid(vecs[0]):
            return vecs[0]
    except Exception:
        pass

    chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE) if text[i:i+CHUNK_SIZE].strip()]
    valid_vecs = []
    for chunk in chunks:
        try:
            vecs = embed_batch([chunk])
            if valid(vecs[0]):
                valid_vecs.append(vecs[0])
        except Exception:
            continue
    if not valid_vecs:
        return None
    dim = len(valid_vecs[0])
    avg = [sum(v[i] for v in valid_vecs) / len(valid_vecs) for i in range(dim)]
    mag = math.sqrt(sum(x * x for x in avg)) or 1.0
    return [x / mag for x in avg]


def fetch_all_faq():
    rows, offset = [], 0
    while True:
        resp = (supabase.table("faq_items")
                .select("id,question,answer,category")
                .range(offset, offset + PAGE_SIZE - 1)
                .execute())
        batch = resp.data or []
        rows.extend(batch)
        print(f"  fetched {len(rows)} rows...", end="\r")
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def build_text(r: dict) -> str:
    return f"Question: {r.get('question','')}\nAnswer: {r.get('answer','')}\nCategory: {r.get('category','')}"


def main():
    print(f"\nRe-embed FAQ items")
    print(f"  Model  : {EMBED_MODEL}  @ {EMBED_URL}")
    print(f"  Target : {SUPABASE_URL}/faq_items")
    print(f"  Dim    : {EMBED_DIM}\n")

    print("Fetching FAQ records from Supabase...")
    rows = fetch_all_faq()
    total = len(rows)
    print(f"Total  : {total} FAQ items\n")

    success, failed, errors = 0, 0, []

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        texts = [build_text(r)[:1200] for r in batch]
        done  = i + len(batch)
        pct   = int(done / total * 100)
        print(f"  [{pct:3d}%] {done}/{total}  embedding {len(batch)} FAQs...", end="\r")

        try:
            for row, text in zip(batch, texts):
                vec = embed_with_fallback(text)
                if not vec:
                    raise ValueError("all chunks produced NaN/invalid embedding")
                supabase.table("faq_items").update({"embedding": vec}).eq("id", row["id"]).execute()
                success += 1
        except Exception as e:
            for row in batch:
                failed += 1
                errors.append({"id": row.get("id"), "error": str(e)})
            time.sleep(1)
            continue

        time.sleep(0.05)

    print(f"\n\nDone!  success={success}  failed={failed}")
    if errors:
        print(f"\nFailed IDs (first 20):")
        for e in errors[:20]:
            print(f"  id={e['id']} — {e['error']}")


if __name__ == "__main__":
    main()
