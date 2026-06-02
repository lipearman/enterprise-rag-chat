"""
Test Thai search quality after bge-m3 re-embedding.
Compares similarity scores for Thai vs unrelated queries.
"""
import os, sys, math, requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")
EMBED_MODEL  = os.getenv("EMBED_MODEL", "bge-m3:latest")

HDR = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

def embed(text):
    r = requests.post(f"{EMBED_URL}/api/embed",
                      json={"model": EMBED_MODEL, "input": [text]},
                      timeout=30)
    r.raise_for_status()
    return r.json()["embeddings"][0]

def search_docs(vec, n=3):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                      headers=HDR,
                      json={"query_embedding": vec, "match_count": n, "filter": {}},
                      timeout=15)
    return r.json() if isinstance(r.json(), list) else []

def search_faq(vec, n=3):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_faq",
                      headers=HDR,
                      json={"query_embedding": vec, "match_count": n},
                      timeout=15)
    return r.json() if isinstance(r.json(), list) else []

queries = [
    ("ประกันภัยรถยนต์",              "Thai: car insurance"),
    ("วิธีการเคลมประกันภัย",          "Thai: how to claim insurance"),
    ("ประกันชีวิต คุ้มครอง",          "Thai: life insurance coverage"),
    ("car insurance coverage",        "English: car insurance"),
    ("สภาพอากาศ ฝนตก",               "Thai: weather rain (unrelated control)"),
]

print("=== Document Search (match_documents) ===\n")
for query, label in queries:
    vec = embed(query)
    results = search_docs(vec, 3)
    print(f"Query: {label!r}")
    for r in results:
        sim   = round(float(r.get("similarity", 0)), 4)
        title = str(r.get("title", "")).strip()[:55]
        head  = str(r.get("heading", "")).strip()[:40]
        print(f"  sim={sim}  {title} / {head}")
    print()

print("\n=== FAQ Search (match_faq) ===\n")
for query, label in queries[:3]:
    vec = embed(query)
    results = search_faq(vec, 3)
    print(f"Query: {label!r}")
    for r in results:
        sim = round(float(r.get("similarity", 0)), 4)
        q   = str(r.get("question", "")).strip()[:70]
        print(f"  sim={sim}  {q}")
    print()
