"""
Quick search test — verifies embedding + Supabase vector retrieval
Run: python test_search.py
"""
import os, sys, json, requests, time
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

EMBED_BASE_URL = os.getenv("OLLAMA_EMBED_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
EMBED_MODEL    = os.getenv("EMBED_MODEL", "mxbai-embed-large:latest")
SUPABASE_URL   = os.getenv("SUPABASE_URL")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY")

HDR = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# ─── helpers ───────────────────────────────────────────────────────────────────

def embed(text: str) -> list:
    r = requests.post(f"{EMBED_BASE_URL}/api/embed",
                      json={"model": EMBED_MODEL, "input": text[:1200]}, timeout=30)
    r.raise_for_status()
    d = r.json()
    return d.get("embeddings", [d.get("embedding")])[0]

def rpc(fn: str, params: dict) -> list:
    r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/{fn}",
                      headers=HDR, json=params, timeout=15)
    r.raise_for_status()
    return r.json() or []

def table_query(tbl: str, filters: dict = None, limit: int = 5) -> list:
    params = f"?limit={limit}"
    if filters:
        for k, v in filters.items():
            params += f"&{k}=eq.{v}"
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{tbl}{params}",
                     headers={**HDR, "Prefer": "count=exact"}, timeout=10)
    r.raise_for_status()
    return r.json() or []

def sep(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def show_result(i: int, row: dict, fields: list):
    print(f"\n  [{i+1}]", end="")
    for f in fields:
        val = str(row.get(f, "")).strip()
        if val:
            label = f.upper()
            print(f"\n      {label}: {val[:120]}", end="")
    print()

# ─── tests ─────────────────────────────────────────────────────────────────────

def test_embed():
    sep("TEST 1 — Embedding (mxbai-embed-large:latest)")
    text = "ประกันภัยรถยนต์คืออะไร"
    print(f"  Input : {text!r}")
    t0 = time.time()
    vec = embed(text)
    ms = int((time.time() - t0) * 1000)
    print(f"  Dim   : {len(vec)}")
    print(f"  Sample: {[round(x,4) for x in vec[:5]]}...")
    print(f"  Time  : {ms} ms")
    assert len(vec) == 1024, f"Expected 1024, got {len(vec)}"
    print("  ✓ PASS")
    return vec

def test_faq_search(queries: list):
    sep("TEST 2 — FAQ Vector Search")
    for q in queries:
        print(f"\n  Query: {q!r}")
        t0 = time.time()
        vec = embed(q)
        rows = rpc("match_faq", {"query_embedding": vec, "match_count": 3})
        ms = int((time.time() - t0) * 1000)
        print(f"  Found {len(rows)} results ({ms} ms)")
        for i, r in enumerate(rows):
            sim = round(float(r.get("similarity", 0)), 4)
            q_text  = str(r.get("question", "")).strip()[:100]
            a_text  = str(r.get("answer",   "")).strip()[:100]
            print(f"    [{i+1}] sim={sim}  Q: {q_text}")
            print(f"          A: {a_text}")
    print("\n  ✓ PASS")

def test_doc_search(queries: list):
    sep("TEST 3 — Document Vector Search")
    for q in queries:
        print(f"\n  Query: {q!r}")
        t0 = time.time()
        vec = embed(q)
        rows = rpc("match_documents", {"query_embedding": vec, "match_count": 3, "filter": {}})
        ms = int((time.time() - t0) * 1000)
        print(f"  Found {len(rows)} results ({ms} ms)")
        for i, r in enumerate(rows):
            sim     = round(float(r.get("similarity", 0)), 4)
            title   = str(r.get("title",   "")).strip()[:60]
            heading = str(r.get("heading", "")).strip()[:60]
            content = str(r.get("content", "")).strip()[:120]
            url     = str(r.get("url",     "")).strip()
            print(f"    [{i+1}] sim={sim}  {title} / {heading}")
            print(f"          {content}")
            print(f"          URL: {url}")
    print("\n  ✓ PASS")

def test_facts_search():
    sep("TEST 4 — Company Facts (keyword match)")
    fact_types = ["phone", "email", "address", "company_name"]
    for ft in fact_types:
        rows = table_query("company_facts", {"fact_type": ft}, limit=3)
        print(f"\n  Type [{ft}] — {len(rows)} rows")
        for r in rows:
            print(f"    • {r.get('fact_value','')[:80]}  (src: {r.get('source_url','')[:50]})")
    print("\n  ✓ PASS")

def test_staff_search():
    sep("TEST 5 — Staff Contacts")
    rows = table_query("staff_contacts", limit=5)
    print(f"  Total sample: {len(rows)} rows")
    for r in rows:
        name  = r.get("name", "")
        pos   = r.get("position", "")
        dept  = r.get("department", "")
        email = r.get("email", "")
        phone = r.get("phone", "")
        print(f"    • {name} | {pos} | {dept} | {email} | {phone}")
    print("\n  ✓ PASS")

# ─── main ──────────────────────────────────────────────────────────────────────

QUERIES_TH = [
    "ประกันภัยรถยนต์ราคาเท่าไหร่",
    "เบี้ยประกันสุขภาพ",
    "วิธีการเคลมประกัน",
]
QUERIES_EN = [
    "motor insurance coverage",
    "health insurance benefits",
]

print("\n" + "="*60)
print("  Enterprise RAG — Search Test")
print(f"  Embed : {EMBED_BASE_URL}  [{EMBED_MODEL}]")
print(f"  DB    : {SUPABASE_URL}")
print("="*60)

try:
    test_embed()
    test_faq_search(QUERIES_TH[:2] + QUERIES_EN[:1])
    test_doc_search(QUERIES_TH[:2] + QUERIES_EN[:1])
    test_facts_search()
    test_staff_search()

    print("\n" + "="*60)
    print("  ALL TESTS PASSED ✓")
    print("="*60 + "\n")

except Exception as e:
    print(f"\n  ✗ FAILED: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)
