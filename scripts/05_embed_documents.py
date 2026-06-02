from _common import CRAWL_DIR, get_embedding, read_jsonl, clean_text, EMBED_DIMENSION
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client
from tqdm import tqdm
import os, json, time, math

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
INPUT = f"{CRAWL_DIR}/chunks.jsonl"
REPORT = f"{CRAWL_DIR}/embed_documents_report.json"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def valid_embedding(e):
    return e and len(e)==EMBED_DIMENSION and not any((v is None or (isinstance(v,float) and (math.isnan(v) or math.isinf(v)))) for v in e)

COMPANY_CODE = os.getenv("COMPANY_CODE", "")

def main():
    rows = read_jsonl(INPUT)
    success, failed, failed_rows = 0,0,[]
    for r in tqdm(rows):
        try:
            text = r.get("text_for_embedding") or r.get("content") or ""
            emb = get_embedding(text, 1800)
            if not valid_embedding(emb): raise Exception(f"bad dim {len(emb) if emb else 0}")
            payload = {k:r.get(k) for k in ["id","url","title","heading","language","category","service","topic","page_type","chunk_index","chunk_size","content","text_for_embedding"]}
            payload["heading_path"] = r.get("heading_path", [])
            payload["keywords"] = r.get("keywords", [])
            payload["suggested_questions"] = r.get("suggested_questions", [])
            payload["embedding"] = emb
            if COMPANY_CODE:
                payload["company_code"] = COMPANY_CODE
            supabase.table("documents").upsert(payload).execute()
            success += 1
            time.sleep(0.03)
        except Exception as e:
            failed += 1
            failed_rows.append({"id":r.get("id"),"url":r.get("url"),"error":str(e)})
    report = {"input":INPUT,"success":success,"failed":failed,"failed_rows":failed_rows}
    open(REPORT,"w",encoding="utf-8").write(json.dumps(report,ensure_ascii=False,indent=2))
    print("DONE", report)

if __name__ == "__main__":
    main()
