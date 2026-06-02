from _common import CRAWL_DIR, read_jsonl
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client
from tqdm import tqdm
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

COMPANY_CODE = os.getenv("COMPANY_CODE", "")

def main():
    for r in tqdm(read_jsonl(f"{CRAWL_DIR}/facts.jsonl")):
        if COMPANY_CODE:
            r["company_code"] = COMPANY_CODE
        supabase.table("company_facts").insert(r).execute()
    for r in tqdm(read_jsonl(f"{CRAWL_DIR}/staff.jsonl")):
        if COMPANY_CODE:
            r["company_code"] = COMPANY_CODE
        supabase.table("staff_contacts").insert(r).execute()
    print("DONE")

if __name__ == "__main__":
    main()
