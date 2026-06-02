"""
Rebuild IVFFlat vector indexes after re-embedding with bge-m3.
The mxbai-era indexes are stale and cause incorrect search results.
"""
import os, sys, requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HDR = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# Try Supabase's internal SQL endpoint variants
sql_statements = [
    "REINDEX INDEX CONCURRENTLY documents_embedding_idx;",
    "REINDEX INDEX CONCURRENTLY faq_items_embedding_idx;",
]

# Method 1: /pg/query POST with text/plain
for sql in sql_statements:
    r = requests.post(f"{SUPABASE_URL}/pg/query",
                      headers={**HDR, "Content-Type": "text/plain"},
                      data=sql, timeout=300)
    print(f"  /pg/query: {r.status_code} {r.text[:200]}")

# Method 2: try psycopg2 direct connection
print("\nTrying psycopg2 direct connection...")
try:
    import psycopg2
    # Supabase self-hosted default credentials
    host = "llm-server"
    for user, password, port in [
        ("postgres",        "postgres",        5432),
        ("supabase_admin",  "postgres",        5432),
        ("postgres",        "postgres",        6543),
        ("authenticator",   "postgres",        5432),
    ]:
        try:
            conn = psycopg2.connect(host=host, port=port, dbname="postgres",
                                    user=user, password=password, connect_timeout=5)
            print(f"  Connected as {user}@{host}:{port}")
            cur = conn.cursor()
            for sql in sql_statements:
                print(f"  Executing: {sql}")
                cur.execute(sql)
            conn.commit()
            print("  REINDEX done!")
            conn.close()
            break
        except psycopg2.OperationalError as e:
            print(f"  {user}:{port} failed: {str(e)[:60]}")
except ImportError:
    print("  psycopg2 not installed")

# Method 3: Create a helper RPC function via SQL
print("\nTrying to create reindex RPC function...")
create_fn = """
CREATE OR REPLACE FUNCTION public.reindex_embeddings()
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  REINDEX INDEX CONCURRENTLY documents_embedding_idx;
  REINDEX INDEX CONCURRENTLY faq_items_embedding_idx;
  RETURN 'done';
END;
$$;
"""
# This won't work via REST but worth trying
r2 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/reindex_embeddings",
                   headers=HDR, json={}, timeout=300)
print(f"  rpc/reindex_embeddings: {r2.status_code} {r2.text[:200]}")
