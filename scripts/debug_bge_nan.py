"""
Investigate bge-m3 NaN:
1. How many docs are Thai vs English?
2. Does stripping to single sentences help?
3. Can we identify the NaN-triggering token?
"""
import os, sys, math, requests, re
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")
EMBED_MODEL  = "bge-m3:latest"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def embed(text):
    r = requests.post(f"{EMBED_URL}/api/embed",
                      json={"model": EMBED_MODEL, "input": [text]},
                      timeout=30)
    if r.status_code != 200:
        return None, r.text[:100]
    return r.json()["embeddings"][0], None

def has_thai(text):
    return bool(re.search(r"[฀-๿]", text))

# --- Part 1: sample 100 docs, count Thai vs English ---
resp = supabase.table("documents").select("id,text_for_embedding,content").range(0, 99).execute()
rows = resp.data
thai_count = sum(1 for r in rows if has_thai((r.get("text_for_embedding") or r.get("content") or "")))
print(f"Sample (rows 0-99): {thai_count}/100 are Thai, {100-thai_count}/100 are English\n")

# --- Part 2: check rows 800-900 (where failures were) ---
resp2 = supabase.table("documents").select("id,text_for_embedding").range(800, 899).execute()
rows2 = resp2.data
thai2 = sum(1 for r in rows2 if has_thai((r.get("text_for_embedding") or "")))
print(f"Sample (rows 800-899): {thai2}/100 Thai, {100-thai2}/100 English\n")

# --- Part 3: test single-sentence approach for failing English docs ---
resp3 = supabase.table("documents").select("id,text_for_embedding").range(834, 838).execute()
rows3 = resp3.data

print("=== Single-sentence fix attempt ===")
for row in rows3:
    raw = (row.get("text_for_embedding") or "").replace("\x00", "")
    rid = row["id"][:12]

    # Split into sentences and try each
    # Remove metadata lines first
    content_lines = [l for l in raw.split("\n")
                     if l.strip() and not any(l.startswith(p) for p in
                        ("Title:","Heading:","Service:","Language:","Keywords:"))]
    content = " ".join(content_lines)

    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    print(f"Doc {rid}: {len(sentences)} sentences, content_len={len(content)}")
    if sentences:
        first_sent = sentences[0]
        print(f"  First sentence ({len(first_sent)} chars): {first_sent[:80]}")
        vec, err = embed(first_sent)
        print(f"  First sentence embed: {'OK' if vec else 'NaN: '+str(err)}")

        # Try combining first 3 sentences
        combined = " ".join(sentences[:3])
        vec2, err2 = embed(combined[:500])
        print(f"  First 3 sentences ({len(combined)} chars): {'OK' if vec2 else 'NaN: '+str(err2)}")
    print()

# --- Part 4: binary search on "The quick brown fox" to confirm NaN is content-specific ---
print("=== NaN pattern investigation ===")
fox = "The quick brown fox jumps over the lazy dog. "
tests = [
    ("fox × 5 (225 chars)", fox * 5),
    ("fox × 6 (270 chars)", fox * 6),
    ("fox × 11 (495 chars)", fox * 11),
    ("'a' × 300", "a" * 300),
    ("'Wattana' × 20", "Wattana " * 20),
    ("'Insurance' × 20", "Insurance " * 20),
    ("'Lockton Wattana Insurance' × 10", "Lockton Wattana Insurance " * 10),
]
for label, text in tests:
    vec, err = embed(text[:500])
    print(f"  {label:40s}: {'OK' if vec else 'NaN'}")
