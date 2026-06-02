# -*- coding: utf-8 -*-
import sys, os, requests, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from _common import CRAWL_DIR, EMBED_BASE_URL, EMBED_MODEL, clean_text, read_jsonl

chunks = read_jsonl(f"{CRAWL_DIR}/chunks.jsonl")
r = chunks[0]
text = r.get("text_for_embedding") or r.get("content") or ""
cleaned = clean_text(text)[:1800]

print(f"url: {r.get('url')}")
print(f"text_for_embedding:\n{repr(cleaned[:500])}")
print()
print(f"--- Sending to embed ---")

try:
    res = requests.post(
        f"{EMBED_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": cleaned},
        timeout=30
    )
    print(f"status: {res.status_code}")
    if res.status_code != 200:
        print(f"error body: {res.text[:500]}")
    else:
        data = res.json()
        emb = data.get("embeddings", [[]])[0]
        print(f"embed dim: {len(emb)}")
except Exception as e:
    print(f"FAIL: {e}")
