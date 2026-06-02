"""
Investigate why match_documents returns 0 for car insurance query.
Check if query embedding has NaN/Inf that breaks pgvector.
"""
import os, sys, math, json, requests
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
    r.raise_for_status()
    return r.json()["embeddings"][0]

def check_vec(vec, label):
    nan_count = sum(1 for v in vec if math.isnan(v))
    inf_count = sum(1 for v in vec if math.isinf(v))
    mag = math.sqrt(sum(v*v for v in vec if not math.isnan(v)))
    print(f"  {label}: dim={len(vec)} nan={nan_count} inf={inf_count} mag={mag:.4f}")
    return nan_count == 0 and inf_count == 0

def rpc_search(vec, label, n=5):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                      headers=HDR,
                      json={"query_embedding": vec, "match_count": n, "filter": {}},
                      timeout=15)
    resp = r.json()
    if isinstance(resp, list):
        print(f"  {label}: {len(resp)} results, first_sim={round(float(resp[0].get('similarity',0)),4) if resp else 'n/a'}")
    else:
        print(f"  {label}: ERROR {r.status_code} {str(resp)[:100]}")
    return resp

# Check query embeddings
queries = [
    "ประกันภัยรถยนต์",
    "วิธีการเคลมประกันภัย",
    "car insurance",
    "motor insurance thailand",
]

print("=== Query vector health check ===")
vecs = {}
for q in queries:
    vec = embed(q)
    ok = check_vec(vec, repr(q)[:35])
    vecs[q] = vec

print("\n=== RPC results ===")
for q, vec in vecs.items():
    rpc_search(vec, repr(q)[:35])

print("\n=== Raw RPC response for car insurance ===")
r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                  headers=HDR,
                  json={"query_embedding": vecs["ประกันภัยรถยนต์"], "match_count": 3, "filter": {}},
                  timeout=15)
print(f"Status: {r.status_code}")
print(f"Response type: {type(r.json()).__name__}")
print(f"Response: {str(r.json())[:300]}")
