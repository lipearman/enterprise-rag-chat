"""
Binary-search for the exact character position that causes bge-m3 500.
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

def try_embed(text):
    try:
        r = requests.post(f"{EMBED_URL}/api/embed",
                          json={"model": EMBED_MODEL, "input": [text]},
                          timeout=30)
        r.raise_for_status()
        return True
    except:
        return False

resp = supabase.table("documents").select("id,text_for_embedding").range(834, 834).execute()
row  = resp.data[0]
raw  = (row.get("text_for_embedding") or "").replace("\x00", "")

print(f"id={row['id']}  len={len(raw)}")
print(f"repr[190:220]: {repr(raw[190:220])}")
print()

# Binary search for breaking point
lo, hi = 200, 500
while lo < hi - 1:
    mid = (lo + hi) // 2
    ok = try_embed(raw[:mid])
    print(f"  [{lo}–{hi}] mid={mid} -> {'OK' if ok else 'FAIL'}")
    if ok:
        lo = mid
    else:
        hi = mid

print(f"\nBreaks at length > {lo}")
print(f"Char at position {lo}: {repr(raw[lo])}")
print(f"Context [{lo-5}:{lo+10}]: {repr(raw[lo-5:lo+10])}")

# List all non-ASCII chars in the text and their positions
print("\nAll non-ASCII chars in text:")
for i, ch in enumerate(raw):
    if ord(ch) > 127:
        print(f"  pos={i}  U+{ord(ch):04X}  repr={repr(ch)}")
