# -*- coding: utf-8 -*-
import sys, os, requests
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from _common import EMBED_BASE_URL, EMBED_MODEL, clean_text

print(f"EMBED_BASE_URL = {EMBED_BASE_URL}")
print(f"EMBED_MODEL = {EMBED_MODEL}")

text = clean_text("test embedding hello world")[:1800]
print(f"sending text: {repr(text[:50])}")

try:
    res = requests.post(
        f"{EMBED_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=30
    )
    print(f"status: {res.status_code}")
    print(f"response: {res.text[:200]}")
    res.raise_for_status()
    data = res.json()
    emb = data.get("embeddings", [[]])[0]
    print(f"embed dim: {len(emb)}")
except Exception as e:
    print(f"FAIL: {e}")
