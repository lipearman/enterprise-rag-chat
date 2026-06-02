"""Check match_documents and match_faq function definitions in Supabase."""
import os, sys, requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HDR = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# Query the pg_proc system table for the function definitions
r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                  headers=HDR,
                  json={"query_embedding": [0.0]*1024, "match_count": 1, "filter": {}},
                  timeout=10)
print(f"match_documents test: {r.status_code} len={len(r.json() if isinstance(r.json(), list) else [])}")

# Use the pg_get_functiondef SQL via RPC to get function source
sql_payload = {
    "query": """
        SELECT routine_name, routine_definition
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_name IN ('match_documents', 'match_faq')
        ORDER BY routine_name
    """
}
# Try via PostgREST's SQL endpoint if available
r2 = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                   headers=HDR, json=sql_payload, timeout=10)
print(f"\nSQL exec: {r2.status_code} {r2.text[:200]}")

# Try direct SQL via supabase-js style
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=HDR, timeout=10)
print(f"\nREST root: {r3.status_code} {r3.text[:300]}")
