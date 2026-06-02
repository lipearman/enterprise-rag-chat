"""
Test nomic-embed-text Thai semantic quality.
Writes results to file to avoid CP1252 console encoding issues.
"""
import os, sys, math, requests
from pathlib import Path
from dotenv import load_dotenv

# force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(Path(__file__).parent / ".env")
EMBED_URL = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")

def embed(text, model):
    r = requests.post(f"{EMBED_URL}/api/embed",
                      json={"model": model, "input": [text]},
                      timeout=30)
    if r.status_code != 200:
        return None
    return r.json()["embeddings"][0]

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    ma  = math.sqrt(sum(x*x for x in a))
    mb  = math.sqrt(sum(x*x for x in b))
    return dot / (ma * mb + 1e-10)

pairs = [
    # Thai auto-insurance query vs English auto-insurance doc (cross-lingual: should be HIGH)
    ("ประกันภัยรถยนต์",              "car insurance coverage"),
    # Thai claim query vs English claim doc
    ("วิธีการเคลมประกันภัย",          "how to make an insurance claim"),
    # Thai auto vs Thai life (different topics: should be LOWER)
    ("ประกันภัยรถยนต์",              "ประกันชีวิต"),
    # Thai auto vs Thai auto (same: should be HIGHEST)
    ("ประกันภัยรถยนต์",              "ประกันภัยรถยนต์คุ้มครองความเสียหาย"),
    # Unrelated control: car vs weather (should be LOWEST)
    ("ประกันภัยรถยนต์",              "สภาพอากาศวันนี้"),
]

print("=== nomic-embed-text:latest ===")
for t1, t2 in pairs:
    v1 = embed(t1, "nomic-embed-text:latest")
    v2 = embed(t2, "nomic-embed-text:latest")
    if v1 and v2:
        sim = cosine(v1, v2)
        print(f"  sim={sim:.4f}  '{t1}' × '{t2}'")

print("\n=== bge-m3:latest (Thai only, for comparison) ===")
thai_only_pairs = [
    ("ประกันภัยรถยนต์",              "ประกันชีวิต"),
    ("ประกันภัยรถยนต์",              "ประกันภัยรถยนต์คุ้มครองความเสียหาย"),
    ("ประกันภัยรถยนต์",              "สภาพอากาศวันนี้"),
]
for t1, t2 in thai_only_pairs:
    v1 = embed(t1, "bge-m3:latest")
    v2 = embed(t2, "bge-m3:latest")
    if v1 and v2:
        sim = cosine(v1, v2)
        print(f"  sim={sim:.4f}  '{t1}' × '{t2}'")
