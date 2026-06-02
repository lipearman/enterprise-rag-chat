"""
Test if passing num_ctx in options bypasses the 256-token limit.
"""
import os, requests
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent / ".env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")
EMBED_MODEL  = os.getenv("EMBED_MODEL", "bge-m3:latest")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def embed(text, ctx=None):
    payload = {"model": EMBED_MODEL, "input": [text]}
    if ctx:
        payload["options"] = {"num_ctx": ctx}
    try:
        r = requests.post(f"{EMBED_URL}/api/embed", json=payload, timeout=60)
        r.raise_for_status()
        return True, len(r.json()["embeddings"][0])
    except Exception as e:
        return False, str(e)

resp = supabase.table("documents").select("id,text_for_embedding").range(834, 834).execute()
raw  = (resp.data[0].get("text_for_embedding") or "").replace("\x00", "")
print(f"Text length: {len(raw)}\n")

for ctx in [None, 512, 1024, 4096, 8192]:
    label = f"num_ctx={ctx}" if ctx else "default"
    ok, res = embed(raw[:500], ctx)
    print(f"  500 chars  {label:15s}: {'OK dim='+str(res) if ok else 'FAIL: '+str(res)}")

print()
# Also test full text with ctx=8192
ok, res = embed(raw, 8192)
print(f"  Full text  num_ctx=8192   : {'OK dim='+str(res) if ok else 'FAIL: '+str(res)}")

# Test 1800-char text with ctx=8192
long_text = raw * 2  # ~1746 chars
ok, res = embed(long_text[:1800], 8192)
print(f"  1800 chars num_ctx=8192   : {'OK dim='+str(res) if ok else 'FAIL: '+str(res)}")
