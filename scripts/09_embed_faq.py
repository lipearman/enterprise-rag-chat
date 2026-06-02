from _common import CRAWL_DIR, read_jsonl, get_embedding
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client
from tqdm import tqdm
import os, time

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
INPUT = f"{CRAWL_DIR}/faq_items.jsonl"

COMPANY_CODE = os.getenv("COMPANY_CODE", "")

def main():
    for r in tqdm(read_jsonl(INPUT)):
        text = f"Question: {r.get('question')}\nAnswer: {r.get('answer')}\nCategory: {r.get('category')}"
        emb = get_embedding(text, 1200)
        payload = dict(r); payload["embedding"] = emb
        if COMPANY_CODE:
            payload["company_code"] = COMPANY_CODE
        supabase.table("faq_items").insert(payload).execute()
        time.sleep(0.03)
    print("DONE")

if __name__ == "__main__":
    main()
