"""Check match_documents RPC threshold and raw similarity for car insurance query."""
import os, sys, requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")
EMBED_MODEL  = os.getenv("EMBED_MODEL", "bge-m3:latest")
HDR = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

def embed(text):
    r = requests.post(f"{EMBED_URL}/api/embed", json={"model": EMBED_MODEL, "input": [text]}, timeout=30)
    return r.json()["embeddings"][0]

# Check the RPC definition
r = requests.get(f"{SUPABASE_URL}/rest/v1/rpc/match_documents", headers=HDR, timeout=10)
print(f"GET match_documents: {r.status_code} {r.text[:200]}")
print()

# Try match_documents with match_threshold=0.0 (no threshold)
vec = embed("ประกันภัยรถยนต์")
r2 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                   headers=HDR,
                   json={"query_embedding": vec, "match_count": 5, "filter": {}, "match_threshold": 0.0},
                   timeout=15)
print(f"With match_threshold=0.0: status={r2.status_code}")
results = r2.json() if isinstance(r2.json(), list) else []
for r in results[:5]:
    sim = round(float(r.get("similarity", 0)), 4)
    title = str(r.get("title", "")).strip()[:60]
    print(f"  sim={sim}  {title}")
print()

# Try without match_threshold (default)
r3 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                   headers=HDR,
                   json={"query_embedding": vec, "match_count": 5, "filter": {}},
                   timeout=15)
print(f"Without match_threshold: status={r3.status_code}")
results3 = r3.json() if isinstance(r3.json(), list) else []
for r in results3[:5]:
    sim = round(float(r.get("similarity", 0)), 4)
    title = str(r.get("title", "")).strip()[:60]
    print(f"  sim={sim}  {title}")
