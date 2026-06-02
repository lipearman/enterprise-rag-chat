"""Check if null metadata causes filter:{} to exclude documents."""
import os, sys, requests
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")
EMBED_MODEL  = os.getenv("EMBED_MODEL", "bge-m3:latest")
HDR = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def embed(text):
    r = requests.post(f"{EMBED_URL}/api/embed", json={"model": EMBED_MODEL, "input": [text]}, timeout=30)
    return r.json()["embeddings"][0]

# Check metadata field for motor insurance vs Deves docs
print("=== Metadata check ===")
resp_motor = supabase.table("documents").select("id,title,metadata").ilike("title", "%Motor Insurance%").limit(3).execute()
for doc in resp_motor.data:
    print(f"  Motor: {doc['id'][:12]} metadata={doc.get('metadata')}")

resp_deves = supabase.table("documents").select("id,title,metadata").ilike("title", "%Deves%").limit(3).execute()
for doc in resp_deves.data:
    print(f"  Deves: {doc['id'][:12]} metadata={doc.get('metadata')}")

print()
# Try match_documents WITHOUT filter (to confirm it's the filter causing issues)
vec = embed("ประกันภัยรถยนต์")

# Some RPC functions accept filter as optional - try null
r1 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                   headers=HDR,
                   json={"query_embedding": vec, "match_count": 5},
                   timeout=15)
print(f"No filter:        {r1.status_code} -> {len(r1.json() if isinstance(r1.json(), list) else [])} results")

r2 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                   headers=HDR,
                   json={"query_embedding": vec, "match_count": 5, "filter": {}},
                   timeout=15)
res2 = r2.json() if isinstance(r2.json(), list) else []
print(f"filter={{}}:        {r2.status_code} -> {len(res2)} results")
for r in res2[:3]:
    print(f"  sim={round(float(r.get('similarity',0)),4)}  {str(r.get('title',''))[:50]}")

r3 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                   headers=HDR,
                   json={"query_embedding": vec, "match_count": 5, "filter": None},
                   timeout=15)
print(f"filter=null:      {r3.status_code} -> {len(r3.json() if isinstance(r3.json(), list) else [])} results")
