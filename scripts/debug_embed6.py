# -*- coding: utf-8 -*-
import sys, requests, math
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from _common import CRAWL_DIR, EMBED_BASE_URL, EMBED_MODEL, clean_text, read_jsonl

chunks = read_jsonl(f"{CRAWL_DIR}/chunks.jsonl")

for i, r in enumerate(chunks[:10], 1):
    text_full = clean_text(r.get("text_for_embedding") or "")[:1800]
    text_content = clean_text(r.get("content") or "")[:1200]

    # Try content only
    status_content = "N/A"
    if text_content:
        res = requests.post(f"{EMBED_BASE_URL}/api/embed",
                           json={"model": EMBED_MODEL, "input": text_content}, timeout=10)
        status_content = f"OK dim={len(res.json().get('embeddings',[[]])[0])}" if res.status_code==200 else f"FAIL {res.text[:50]}"

    print(f"Chunk {i}: url={r.get('url','')[-40:]}")
    print(f"  content_len={len(text_content)}, content_status={status_content}")
