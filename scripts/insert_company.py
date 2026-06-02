"""Insert mgcars into companies table."""
import os, requests, json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")
URL = os.getenv("SUPABASE_URL", "")
KEY = os.getenv("SUPABASE_KEY", "")
HDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

sql = """
INSERT INTO companies (company_code, company_name, base_url, is_active)
VALUES ('mgcars', 'MG Cars Thailand', 'https://www.mgcars.com', true)
ON CONFLICT (company_code) DO UPDATE
  SET company_name = EXCLUDED.company_name,
      base_url     = EXCLUDED.base_url,
      is_active    = EXCLUDED.is_active,
      updated_at   = now();
"""
r = requests.post(f"{URL}/pg/query", headers=HDR, json={"query": sql}, timeout=10)
print("INSERT result:", r.status_code, r.text[:200])

# verify
r2 = requests.post(f"{URL}/pg/query", headers=HDR,
                   json={"query": "SELECT company_code, company_name, base_url, is_active FROM companies ORDER BY company_code;"},
                   timeout=10)
print("\nAll companies:")
for row in r2.json():
    print(f"  {row['company_code']:20} | {row['company_name']:30} | {row['base_url']} | active={row['is_active']}")
