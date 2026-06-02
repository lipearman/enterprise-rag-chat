"""
Test workarounds for bge-m3 NaN on English text.
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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def embed(text, model="bge-m3:latest"):
    r = requests.post(f"{EMBED_URL}/api/embed",
                      json={"model": model, "input": [text]},
                      timeout=30)
    if r.status_code != 200:
        return None, r.text[:80]
    return r.json()["embeddings"][0], None

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a, b))
    ma = math.sqrt(sum(x*x for x in a))
    mb = math.sqrt(sum(x*x for x in b))
    return dot/(ma*mb+1e-10)

# Fetch two failing English docs
resp = supabase.table("documents").select("id,text_for_embedding,content").range(834, 835).execute()
rows = resp.data

for row in rows:
    raw_embed = (row.get("text_for_embedding") or "")
    raw_content = (row.get("content") or "")
    rid = row["id"][:12]
    print(f"=== Doc {rid} ===")
    print(f"  text_for_embedding len={len(raw_embed)}")
    print(f"  content len={len(raw_content)}")
    print(f"  content[:120]: {repr(raw_content[:120])}")
    print()

    # Test 1: use content field directly
    vec, err = embed(raw_content[:500])
    print(f"  content[:500]: {'OK' if vec else 'NaN'}")

    # Test 2: use only first 200 chars (known-good threshold)
    vec, err = embed(raw_embed[:200])
    print(f"  text_for_embedding[:200]: {'OK' if vec else 'NaN'}")

    # Test 3: chunk into 150-char pieces, average
    chunks = [raw_embed[i:i+150] for i in range(0, min(len(raw_embed), 1800), 150)]
    vecs = []
    for chunk in chunks:
        v, e = embed(chunk)
        if v and not any(math.isnan(x) for x in v):
            vecs.append(v)
    if vecs:
        # average the chunk embeddings
        avg = [sum(v[i] for v in vecs)/len(vecs) for i in range(len(vecs[0]))]
        # renormalize
        mag = math.sqrt(sum(x*x for x in avg))
        avg_norm = [x/mag for x in avg]
        print(f"  chunk-avg ({len(vecs)}/{len(chunks)} chunks OK): OK dim={len(avg_norm)}")
    else:
        print(f"  chunk-avg: all chunks failed")

    # Test 4: identify which specific words/tokens trigger NaN
    # Test if removing spaces helps
    no_spaces = raw_embed[:500].replace(" ", "_")
    vec, err = embed(no_spaces)
    print(f"  spaces→underscore: {'OK' if vec else 'NaN'}")

    # Test if adding Thai prefix helps
    thai_prefix = "เนื้อหาภาษาอังกฤษ: " + raw_embed[:400]
    vec, err = embed(thai_prefix)
    print(f"  Thai prefix+400: {'OK' if vec else 'NaN'}")
    print()

# --- Identify the problematic token ---
print("=== Token pattern investigation ===")
fox_words = ["The", "quick", "brown", "fox", "jumps", "over", "lazy", "dog"]
sentence   = "The quick brown fox jumps over the lazy dog."
for word in fox_words:
    v, e = embed(word * 50)
    print(f"  '{word}' × 50 ({len(word)*50} chars): {'OK' if v else 'NaN'}")

# Test combinations
for combo in [
    "The quick",
    "quick brown fox",
    "jumps over the lazy",
    "fox jumps over",
    "The quick brown fox jumps",
    sentence,
    sentence * 2,
    sentence * 3,
]:
    v, e = embed(combo)
    status = 'OK' if v else 'NaN'
    print(f"  [{status}] {repr(combo[:60])}")
