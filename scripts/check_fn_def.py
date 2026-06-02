"""Get match_documents function definition via pg_catalog."""
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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def embed(text):
    r = requests.post(f"{EMBED_URL}/api/embed", json={"model": EMBED_MODEL, "input": [text]}, timeout=30)
    return r.json()["embeddings"][0]

# Check what car insurance docs we have in the DB
resp = supabase.table("documents").select("id,title,heading,text_for_embedding").ilike("text_for_embedding", "%ประกันภัยรถยนต์%").limit(5).execute()
print(f"Docs with 'ประกันภัยรถยนต์' in text: {len(resp.data)}")
for r in resp.data:
    print(f"  {r['id'][:12]} | {str(r.get('title',''))[:50]}")

print()
# Also check English car insurance docs
resp2 = supabase.table("documents").select("id,title,heading").ilike("title", "%motor%").limit(10).execute()
print(f"Docs with 'motor' in title: {len(resp2.data)}")
for r in resp2.data:
    print(f"  {r['id'][:12]} | {r.get('title','')[:60]}")

# Now test the actual similarity scores without threshold
vec = embed("ประกันภัยรถยนต์")
HDR = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# Try with high match_count to see what would come back
r3 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                   headers=HDR,
                   json={"query_embedding": vec, "match_count": 20, "filter": {}},
                   timeout=15)
results = r3.json() if isinstance(r3.json(), list) else []
print(f"\nmatch_documents(ประกันภัยรถยนต์, count=20): {len(results)} results")
for r in results[:5]:
    sim = round(float(r.get("similarity", 0)), 4)
    title = str(r.get("title", "")).strip()[:60]
    print(f"  sim={sim}  {title}")
