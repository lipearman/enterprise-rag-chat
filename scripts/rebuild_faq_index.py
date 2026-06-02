"""Rebuild the FAQ IVFFlat index now that all FAQ items are re-embedded with bge-m3."""
import os, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HDR = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"}

sql = """
DROP INDEX IF EXISTS faq_items_embedding_idx;
CREATE INDEX faq_items_embedding_idx ON faq_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
"""
r = requests.post(f"{SUPABASE_URL}/pg/query", headers=HDR, json={"query": sql}, timeout=300)
print(f"FAQ index rebuild: {r.status_code} {r.text[:200]}")
