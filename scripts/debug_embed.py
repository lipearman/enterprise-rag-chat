"""
Debug why bge-m3:latest returns 500 on actual document texts.
Tests truncation levels, encoding issues, and null bytes.
"""
import os, requests, math
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")
EMBED_MODEL  = os.getenv("EMBED_MODEL", "bge-m3:latest")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def embed(text, model=None):
    m = model or EMBED_MODEL
    try:
        r = requests.post(f"{EMBED_URL}/api/embed",
                          json={"model": m, "input": [text]},
                          timeout=60)
        r.raise_for_status()
        vec = r.json()["embeddings"][0]
        return vec, None
    except Exception as e:
        return None, str(e)

print(f"Embed URL : {EMBED_URL}")
print(f"Model     : {EMBED_MODEL}")
print()

# Fetch docs from around index 834 (where failures were concentrated)
resp = (supabase.table("documents")
        .select("id,text_for_embedding,content")
        .range(834, 840)
        .execute())
rows = resp.data or []
print(f"Fetched {len(rows)} rows (index 834-840)\n")

for i, row in enumerate(rows[:5]):
    raw = row.get("text_for_embedding") or row.get("content") or ""
    rid = row.get("id", "?")
    print(f"--- Row {834+i} | id={rid} | raw_len={len(raw)} ---")

    # Check for problematic characters
    null_count  = raw.count("\x00")
    ctrl_count  = sum(1 for c in raw if ord(c) < 32 and c not in "\n\r\t")
    print(f"  null_bytes={null_count}  other_ctrl={ctrl_count}")
    print(f"  first 120 chars: {repr(raw[:120])}")

    # Test at various truncation lengths
    for length in [50, 200, 500, 1000, 1800]:
        text = raw[:length].replace("\x00", "")  # strip null bytes
        vec, err = embed(text)
        if err:
            print(f"  len={length:4d} -> ERROR: {err}")
        else:
            mag = math.sqrt(sum(v*v for v in vec))
            print(f"  len={length:4d} -> OK  dim={len(vec)}  mag={mag:.4f}")
    print()

# Also test a known-good simple text to confirm model is alive
vec, err = embed("hello world")
print(f"\nSanity check 'hello world': {'OK dim='+str(len(vec)) if vec else 'FAIL: '+str(err)}")
