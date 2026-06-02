"""
1. Test bge-m3 NaN fix via text preprocessing
2. Test nomic-embed-text Thai quality (semantic similarity check)
"""
import os, requests, math
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent / ".env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def embed(text, model):
    r = requests.post(f"{EMBED_URL}/api/embed",
                      json={"model": model, "input": [text]},
                      timeout=30)
    if r.status_code != 200:
        return None, r.text[:120]
    return r.json()["embeddings"][0], None

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    ma  = math.sqrt(sum(x*x for x in a))
    mb  = math.sqrt(sum(x*x for x in b))
    return dot / (ma * mb + 1e-10)

# --- Part 1: bge-m3 NaN fix via preprocessing ---
resp = supabase.table("documents").select("id,text_for_embedding,content").range(834, 836).execute()
rows = resp.data

print("=== Part 1: bge-m3 NaN fix attempts ===\n")
for row in rows:
    raw = (row.get("text_for_embedding") or row.get("content") or "")[:1800]
    rid = row["id"][:12]
    print(f"Doc {rid} (len={len(raw)}):")

    # Try 1: strip metadata prefix (everything before first blank line or after 3rd newline)
    lines = raw.split("\n")
    meta_lines = [l for l in lines if any(l.startswith(p) for p in ("Title:","Heading:","Service:","Language:","Keywords:"))]
    content_lines = [l for l in lines if not any(l.startswith(p) for p in ("Title:","Heading:","Service:","Language:","Keywords:"))]
    content_only = "\n".join(content_lines).strip()[:1800]

    # Try 2: add bge-m3 instruction prefix (it's designed for this)
    with_prefix = "Represent this document for retrieval: " + raw[:1800]

    # Try 3: remove U+2019 and similar smart quotes
    cleaned = raw.replace("’","'").replace("‘","'").replace("“",'"').replace("”",'"')

    for label, text in [
        ("raw[:500]",          raw[:500]),
        ("content_only",       content_only[:500] if content_only else ""),
        ("with_prefix",        with_prefix[:600]),
        ("cleaned",            cleaned[:500]),
    ]:
        if not text:
            continue
        vec, err = embed(text, "bge-m3:latest")
        ok = vec is not None and not any(math.isnan(v) for v in vec)
        print(f"  {label:20s}: {'OK' if ok else 'NaN/ERR: '+str(err)[:60]}")
    print()

# --- Part 2: nomic-embed-text Thai semantic quality ---
print("\n=== Part 2: nomic-embed-text Thai semantic quality ===\n")
thai_pairs = [
    ("ประกันภัยรถยนต์",  "car insurance"),
    ("การเคลมประกัน",    "insurance claim process"),
    ("ประกันภัยรถยนต์",  "ประกันชีวิต"),   # auto vs life insurance (should differ)
    ("ประกันภัยรถยนต์",  "ประกันภัยรถยนต์คุ้มครองรถ"),  # same topic (should be similar)
]

print("  nomic-embed-text Thai cosine similarities:")
for t1, t2 in thai_pairs:
    v1, e1 = embed(t1, "nomic-embed-text:latest")
    v2, e2 = embed(t2, "nomic-embed-text:latest")
    if v1 and v2:
        sim = cosine(v1, v2)
        print(f"  {t1!r:30s} × {t2!r:40s}  sim={sim:.4f}")
    else:
        print(f"  ERROR: {e1 or e2}")

print("\n  bge-m3 Thai cosine similarities (for comparison):")
for t1, t2 in thai_pairs[:2]:
    v1, e1 = embed(t1, "bge-m3:latest")
    v2, e2 = embed(t2, "bge-m3:latest")
    if v1 and v2:
        sim = cosine(v1, v2)
        print(f"  {t1!r:30s} × {t2!r:40s}  sim={sim:.4f}")
    else:
        print(f"  ERROR: {e1 or e2}")
