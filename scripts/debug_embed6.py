"""
Capture the actual 500 error body from Ollama + find exact token threshold.
"""
import os, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
EMBED_URL  = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3:latest")

def embed_raw(text, model=None):
    m = model or EMBED_MODEL
    r = requests.post(f"{EMBED_URL}/api/embed",
                      json={"model": m, "input": [text]},
                      timeout=30)
    return r.status_code, r.text[:500]

# Get the actual error message
english_500 = "The quick brown fox jumps over the lazy dog. " * 11
status, body = embed_raw(english_500[:500])
print(f"English 500 chars: status={status}")
print(f"Response body: {body}")
print()

# Find exact char boundary for ASCII
for n in [200, 240, 250, 256, 257, 258, 260, 300]:
    text = "a" * n
    status, body = embed_raw(text)
    ok = "embeddings" in body
    print(f"  {n} × 'a': status={status}  {'OK' if ok else 'FAIL: '+body[:80]}")

print()
# Find exact char boundary for Thai
thai_unit = "ก"  # single Thai char (3 UTF-8 bytes)
for n in [100, 200, 256, 300, 400, 500, 600]:
    text = thai_unit * n
    status, body = embed_raw(text)
    ok = "embeddings" in body
    print(f"  {n} × Thai 'ก': status={status}  {'OK' if ok else 'FAIL: '+body[:80]}")
