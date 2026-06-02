"""Insert a showroom-finder address fact for mgcars into company_facts."""
import os, requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

URL = os.getenv("SUPABASE_URL", "")
KEY = os.getenv("SUPABASE_KEY", "")
HDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

facts = [
    {
        "fact_type": "address",
        "fact_value": (
            "MG Cars Thailand ไม่มีที่อยู่สำนักงานเดียว "
            "แต่มีโชว์รูมและตัวแทนจำหน่ายทั่วประเทศ "
            "ค้นหาโชว์รูมใกล้บ้านได้ที่ https://www.mgcars.com/th/find-showroom"
        ),
        "language": "th",
        "company_code": "mgcars",
        "confidence": 0.85,
        "source_url": "https://www.mgcars.com/th/find-showroom",
    },
    {
        "fact_type": "address",
        "fact_value": (
            "MG Cars Thailand does not operate from a single headquarters. "
            "Find your nearest showroom or dealer at https://www.mgcars.com/en/find-showroom"
        ),
        "language": "en",
        "company_code": "mgcars",
        "confidence": 0.85,
        "source_url": "https://www.mgcars.com/en/find-showroom",
    },
]

for fact in facts:
    sql = f"""
        INSERT INTO company_facts (fact_type, fact_value, language, company_code, confidence, source_url)
        VALUES (
            '{fact["fact_type"]}',
            $${fact["fact_value"]}$$,
            '{fact["language"]}',
            '{fact["company_code"]}',
            {fact["confidence"]},
            '{fact["source_url"]}'
        )
        ON CONFLICT DO NOTHING;
    """
    r = requests.post(f"{URL}/pg/query", headers=HDR, json={"query": sql}, timeout=15)
    print(f"[{fact['language']}] status={r.status_code} body={r.text[:200]}")

# Verify
verify_sql = "SELECT id, fact_type, fact_value, language FROM company_facts WHERE company_code='mgcars' AND fact_type='address';"
r = requests.post(f"{URL}/pg/query", headers=HDR, json={"query": verify_sql}, timeout=15)
print("\n--- Verification ---")
import json
rows = r.json() if isinstance(r.json(), list) else []
for row in rows:
    print(f"  id={row.get('id')} lang={row.get('language')} value={row.get('fact_value','')[:80]}")
print(f"Total address rows: {len(rows)}")
