# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from _common import CRAWL_DIR, read_jsonl, get_embedding, clean_text

chunks = read_jsonl(f"{CRAWL_DIR}/chunks.jsonl")
print(f"Total chunks: {len(chunks)}")

for i, chunk in enumerate(chunks[:5], 1):
    text = chunk.get("text_for_embedding") or chunk.get("content") or ""
    cleaned = clean_text(text)[:1800]
    print(f"\nChunk {i}: url={chunk.get('url')}")
    print(f"  text_for_embedding len={len(text)}, cleaned len={len(cleaned)}")
    # Check for null bytes or weird chars
    null_count = cleaned.count('\x00')
    print(f"  null bytes={null_count}")
    try:
        e = get_embedding(text, 1800)
        if e:
            print(f"  embed OK dim={len(e)}")
        else:
            print(f"  embed returned None/empty")
    except Exception as ex:
        print(f"  embed FAIL: {ex}")
