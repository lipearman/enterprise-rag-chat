# -*- coding: utf-8 -*-
import sys, requests, math
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from _common import CRAWL_DIR, EMBED_BASE_URL, EMBED_MODEL, clean_text, read_jsonl

def embed_batch(texts):
    """Try embedding a list of texts in a single batch call."""
    res = requests.post(
        f"{EMBED_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": texts},
        timeout=60
    )
    if res.status_code == 200:
        return res.json().get("embeddings", [])
    return None

chunks = read_jsonl(f"{CRAWL_DIR}/chunks.jsonl")
r = chunks[0]

text_full = clean_text(r.get("text_for_embedding") or "")[:1800]
text_content = clean_text(r.get("content") or "")[:1200]
sub_chunks = [text_full[i:i+150] for i in range(0, len(text_full), 150) if text_full[i:i+150].strip()]

print(f"url: {r.get('url')}")
print(f"full text len={len(text_full)}, content len={len(text_content)}, sub_chunks={len(sub_chunks)}")

# Test 1: full text_for_embedding
res = requests.post(f"{EMBED_BASE_URL}/api/embed", json={"model": EMBED_MODEL, "input": text_full}, timeout=30)
print(f"\n1) full text_for_embedding: status={res.status_code}")
if res.status_code != 200: print(f"   error: {res.text[:100]}")

# Test 2: content only
res = requests.post(f"{EMBED_BASE_URL}/api/embed", json={"model": EMBED_MODEL, "input": text_content}, timeout=30)
print(f"2) content only: status={res.status_code}")
if res.status_code != 200: print(f"   error: {res.text[:100]}")

# Test 3: batch sub-chunks in ONE call
result = embed_batch(sub_chunks)
if result is not None:
    print(f"3) batch {len(sub_chunks)} sub-chunks in ONE call: got {len(result)} embeddings")
    valid = [e for e in result if e and not any(math.isnan(v) for v in e)]
    print(f"   valid embeddings: {len(valid)}")
else:
    print(f"3) batch sub-chunks: FAILED")
