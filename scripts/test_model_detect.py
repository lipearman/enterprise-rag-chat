"""
ทดสอบว่า vectors ใน DB ถูก embed ด้วย model ไหน
โดยการ query ด้วยแต่ละ model แล้วดู similarity score
"""
import requests, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")
HDR = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

def embed(model, text):
    r = requests.post(f"{EMBED_URL}/api/embed", json={"model": model, "input": text}, timeout=30)
    return r.json()["embeddings"][0]

def search_docs(vec, n=3):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                      headers=HDR, json={"query_embedding": vec, "match_count": n, "filter": {}}, timeout=15)
    return r.json() or []

def search_faq(vec, n=3):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_faq",
                      headers=HDR, json={"query_embedding": vec, "match_count": n}, timeout=15)
    return r.json() or []

QUERIES = [
    "ประกันภัยรถยนต์",
    "motor insurance coverage",
    "สินไหมทดแทน วิธีเคลม",
]

for model in ["mxbai-embed-large:latest", "bge-m3:latest"]:
    print(f"\n{'='*55}")
    print(f"  MODEL: {model}")
    print('='*55)
    for q in QUERIES:
        vec = embed(model, q)
        docs = search_docs(vec, 2)
        print(f"\n  Query: {q!r}")
        for d in docs:
            sim   = round(float(d.get("similarity", 0)), 4)
            title = str(d.get("title","")).strip()[:50]
            head  = str(d.get("heading","")).strip()[:50]
            print(f"    sim={sim}  {title} / {head}")
