from _common import CRAWL_DIR, read_jsonl, write_jsonl, call_ollama, extract_json_object, clean_text
import time

INPUT = f"{CRAWL_DIR}/chunks.jsonl"
OUTPUT = f"{CRAWL_DIR}/metadata_items.jsonl"

def extract(row):
    prompt = f"""
Extract metadata for Enterprise RAG. Return JSON only:
{{"service":"...","industry":"...","insurance_type":"...","entities":[],"keywords":[],"intent_tags":[]}}

Title:{row.get('title')}
Heading:{row.get('heading')}
Content:{clean_text(row.get('content',''))[:2500]}
"""
    try:
        return extract_json_object(call_ollama(prompt, num_predict=1000)) or {}
    except Exception:
        return {}

def main():
    out = []
    rows = read_jsonl(INPUT)
    for i,r in enumerate(rows,1):
        print(f"[{i}/{len(rows)}]")
        m = extract(r)
        out.append({"document_id":r.get("id"),"url":r.get("url"),"title":r.get("title"),"heading":r.get("heading"),"language":r.get("language"),"category":r.get("category"),"service":m.get("service") or r.get("service"),"topic":m.get("insurance_type") or r.get("topic"),"page_type":r.get("page_type"),"entities":m.get("entities",[]),"keywords":m.get("keywords",[]),"intent_tags":m.get("intent_tags",[])})
        time.sleep(0.15)
    write_jsonl(OUTPUT,out)
    print("DONE", len(out))

if __name__ == "__main__":
    main()
