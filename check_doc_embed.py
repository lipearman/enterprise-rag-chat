"""Check actual embedding format for motor insurance docs."""
import os, sys, math, json, requests
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

def parse_embedding(emb):
    """Parse embedding from whatever format Supabase returns."""
    if isinstance(emb, list):
        return [float(v) for v in emb]
    if isinstance(emb, str):
        # pgvector string format: "[0.1,0.2,...]"
        return [float(v) for v in emb.strip("[]").split(",")]
    return None

# Fetch a motor insurance doc using supabase-py (handles type mapping better)
resp = supabase.table("documents").select("id,title,embedding").ilike("title", "%Motor Insurance%").limit(3).execute()
print(f"Motor insurance docs: {len(resp.data)}")
for doc in resp.data:
    emb_raw = doc.get("embedding")
    emb_type = type(emb_raw).__name__
    emb_len = len(emb_raw) if emb_raw else 0
    print(f"  id={doc['id'][:12]}  emb_type={emb_type}  emb_len={emb_len}")
    print(f"  title: {doc.get('title','')[:60]}")

    emb = parse_embedding(emb_raw)
    if emb:
        # Check if it looks like bge-m3 (mag should be ~1.0) or mxbai (might differ)
        mag = math.sqrt(sum(v*v for v in emb))
        # bge-m3 embeddings have specific value patterns
        # Let's check similarity to "Motor Insurance in Thailand" in both models
        print(f"  embedding mag={mag:.4f}  first3={[round(emb[i],4) for i in range(3)]}")

        # Query similarity
        q_vec = embed("Motor Insurance in Thailand")
        sim = cosine(q_vec, emb)
        print(f"  cosine('Motor Insurance in Thailand', doc_embedding) = {sim:.4f}")

        q_thai = embed("ประกันภัยรถยนต์")
        sim_thai = cosine(q_thai, emb)
        print(f"  cosine('ประกันภัยรถยนต์', doc_embedding) = {sim_thai:.4f}")
    print()

# Now check the 19 failed docs from the log
print("=== Checking some of the 19 failed doc IDs ===")
failed_ids = [
    "dc771e95d01f6d524bdf2984bf2d2004",
    "163de6ebf68a309548e5cb3d9898ecf0",
    "845d374ad52e60ea70e8c14034381f2c",
]
for fid in failed_ids:
    resp2 = supabase.table("documents").select("id,title").eq("id", fid).limit(1).execute()
    if resp2.data:
        print(f"  {fid[:12]}: {resp2.data[0].get('title','')[:60]}")
    else:
        print(f"  {fid[:12]}: not found")
