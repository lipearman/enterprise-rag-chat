"""Quick check: how many documents already have bge-m3 embeddings vs null/old."""
import os, sys, requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HDR = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
       "Content-Type": "application/json"}

# Count total documents
r = requests.get(f"{SUPABASE_URL}/rest/v1/documents",
                 headers={**HDR, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"},
                 timeout=10)
total = int(r.headers.get("content-range", "0/0").split("/")[-1])
print(f"Total documents: {total}")

# Check a sample at different ranges to see if embeddings changed
# (We can't easily detect bge-m3 vs mxbai just from the vector values,
#  but we can see if any have null embeddings and count recently updated)
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/documents?select=id,embedding&embedding=is.null&limit=1",
                  headers=HDR, timeout=10)
print(f"Docs with null embedding: {len(r2.json())}")

# Check the last 5 docs in the table to see if embedding is populated
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/documents?select=id&order=id&limit=5&offset=0",
                  headers=HDR, timeout=10)
print(f"First 5 doc IDs: {[d['id'][:12] for d in r3.json()]}")

# Use an RPC to get count
r4 = requests.get(f"{SUPABASE_URL}/rest/v1/documents?select=count&embedding=not.is.null",
                  headers={**HDR, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"},
                  timeout=10)
total_with_embed = int(r4.headers.get("content-range", "0/0").split("/")[-1])
print(f"Docs with non-null embedding: {total_with_embed}")
