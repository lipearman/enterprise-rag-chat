"""
Bypass the RPC threshold by computing similarity directly.
Also try to get the function source via pg_get_functiondef.
"""
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

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    ma  = math.sqrt(sum(x*x for x in a))
    mb  = math.sqrt(sum(x*x for x in b))
    return dot/(ma*mb+1e-10)

# Get motor insurance doc embeddings directly
doc_ids = ["e1c44b6bcfc0", "c58d4c863fe1", "eca09b481769"]
vec_query = embed("ประกันภัยรถยนต์")

print("Direct similarity (bypassing RPC threshold):")
for did in doc_ids:
    resp = supabase.table("documents").select("id,title,embedding").eq("id", did + "0000000000000000000000"[:32-len(did)]).limit(1).execute()
    # Use ilike on partial id
    resp2 = requests.get(f"{SUPABASE_URL}/rest/v1/documents?id=like.{did}*&select=id,title,embedding&limit=1",
                         headers=HDR, timeout=10)
    if resp2.status_code == 200 and resp2.json():
        doc = resp2.json()[0]
        emb = doc.get("embedding")
        if emb and isinstance(emb, list):
            sim = cosine(vec_query, emb)
            print(f"  sim={sim:.4f}  {doc.get('title','')[:60]}")
        else:
            print(f"  NO EMBEDDING for {doc.get('title','')[:40]}")
    else:
        print(f"  {did}: {resp2.status_code}")

# Try to get the function definition via information_schema
print("\nFunction definition attempt via SQL RPC:")
r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/get_fn_source",
                  headers=HDR, json={"fn_name": "match_documents"}, timeout=10)
print(f"  {r.status_code} {r.text[:200]}")

# Try reading pg_proc directly through Supabase's /pg/query endpoint
r2 = requests.post(f"{SUPABASE_URL}/pg/query",
                   headers={**HDR, "Content-Type": "text/plain"},
                   data="SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname='match_documents'",
                   timeout=10)
print(f"  /pg/query: {r2.status_code} {r2.text[:300]}")
