"""Check table schema and investigate why car insurance query returns 0 results."""
import os, sys, math, requests
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

def parse_embedding(emb):
    if isinstance(emb, list):
        return [float(v) for v in emb]
    if isinstance(emb, str):
        return [float(v) for v in emb.strip("[]").split(",")]
    return None

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    ma  = math.sqrt(sum(x*x for x in a))
    mb  = math.sqrt(sum(x*x for x in b))
    return dot/(ma*mb+1e-10)

# Get the actual columns of documents table
resp = requests.get(f"{SUPABASE_URL}/rest/v1/documents?limit=1", headers=HDR, timeout=10)
doc = resp.json()[0] if resp.json() else {}
print(f"Documents table columns: {list(doc.keys())}")
print()

# Try match_documents with different approaches
vec = embed("ประกันภัยรถยนต์")

# 1. No filter at all
r1 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                   headers=HDR, json={"query_embedding": vec, "match_count": 5}, timeout=15)
res1 = r1.json() if isinstance(r1.json(), list) else []
print(f"1. No filter: {len(res1)} results")
for r in res1[:3]:
    print(f"  sim={round(float(r.get('similarity',0)),4)}  {str(r.get('title',''))[:55]}")

# 2. The claim insurance query that DID work
vec2 = embed("วิธีการเคลมประกันภัย")
r2 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                   headers=HDR, json={"query_embedding": vec2, "match_count": 5, "filter": {}}, timeout=15)
res2 = r2.json() if isinstance(r2.json(), list) else []
print(f"\n2. Claim query with filter={{}}: {len(res2)} results")
for r in res2[:3]:
    print(f"  sim={round(float(r.get('similarity',0)),4)}  {str(r.get('title',''))[:55]}")

# 3. Manually compute cosine for top motor insurance docs
print("\n3. Direct cosine similarity to top motor docs:")
resp_docs = supabase.table("documents").select("id,title,embedding").ilike("title", "%Motor%").limit(5).execute()
for doc in resp_docs.data:
    emb = parse_embedding(doc.get("embedding"))
    if emb:
        sim = cosine(vec, emb)
        mag = math.sqrt(sum(v*v for v in emb))
        print(f"  sim={sim:.4f}  mag={mag:.4f}  {doc.get('title','')[:55]}")

# 4. What does the first query's result set's similarity look like?
print("\n4. claim query similarities (successful results):")
for r in res2[:3]:
    print(f"  sim={round(float(r.get('similarity',0)),4)}")
