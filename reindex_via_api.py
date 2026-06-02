"""
Try multiple Supabase API endpoints to run REINDEX SQL.
"""
import os, sys, json, requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")  # http://llm-server:8000
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HDR_JWT  = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"}
HDR_PLAIN = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY}

reindex_sql = """
DROP INDEX IF EXISTS documents_embedding_idx;
CREATE INDEX documents_embedding_idx ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
DROP INDEX IF EXISTS faq_items_embedding_idx;
CREATE INDEX faq_items_embedding_idx ON faq_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
"""

# Try different endpoint formats
tests = [
    # (method, url, headers, body)
    ("POST", f"{SUPABASE_URL}/pg/query",    HDR_JWT,   {"query": reindex_sql}),
    ("POST", f"{SUPABASE_URL}/pg/query",    HDR_JWT,   {"sql": reindex_sql}),
    ("POST", f"{SUPABASE_URL}/pg/query",    HDR_PLAIN, reindex_sql.encode("utf-8")),
    # Meta API variations
    ("POST", f"{SUPABASE_URL}/rest/v1/rpc/exec_sql", HDR_JWT, {"query": reindex_sql}),
    # Try direct meta endpoint
    ("POST", "http://llm-server:8080/pg/query",  HDR_JWT,  {"query": reindex_sql}),
    ("POST", "http://llm-server:5555/pg/query",  HDR_JWT,  {"query": reindex_sql}),
]

for method, url, hdrs, body in tests:
    try:
        if isinstance(body, bytes):
            r = requests.request(method, url, headers={**hdrs, "Content-Type": "text/plain"}, data=body, timeout=10)
        else:
            r = requests.request(method, url, headers=hdrs, json=body, timeout=10)
        print(f"  {method} {url.replace('http://llm-server','<host>')}: {r.status_code} {r.text[:120]}")
    except Exception as e:
        print(f"  {method} {url.replace('http://llm-server','<host>')}: CONN_ERR {str(e)[:60]}")

# Also try the Supabase CLI approach - check if supabase is installed
import subprocess
result = subprocess.run(["supabase", "db", "push", "--help"], capture_output=True, text=True, timeout=5)
print(f"\nsupabase CLI: {'available' if result.returncode == 0 else 'not available'}")

# Check if psql is available
result2 = subprocess.run(["psql", "--version"], capture_output=True, text=True, timeout=5)
print(f"psql: {'available: '+result2.stdout.strip() if result2.returncode == 0 else 'not available'}")
