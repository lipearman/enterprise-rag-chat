# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from _common import CRAWL_DIR, read_jsonl, get_embedding

chunks = read_jsonl(f"{CRAWL_DIR}/chunks.jsonl")
print(f"Testing {min(5, len(chunks))} chunks with chunk-averaging fallback...")
for i, r in enumerate(chunks[:5], 1):
    text = r.get("text_for_embedding") or r.get("content") or ""
    url = r.get("url", "?")
    try:
        e = get_embedding(text, 1800)
        if e:
            print(f"  Chunk {i} OK dim={len(e)} url={url}")
        else:
            print(f"  Chunk {i} FAIL (None) url={url}")
    except Exception as ex:
        print(f"  Chunk {i} FAIL: {ex} url={url}")
