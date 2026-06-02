from _common import CRAWL_DIR, clean_text, read_jsonl, write_jsonl, call_ollama, extract_json_array, detect_category_rule, detect_language_rule
import time

INPUT = f"{CRAWL_DIR}/clean_sections.jsonl"
OUTPUT = f"{CRAWL_DIR}/faq_items.jsonl"

def gen(row):
    content = clean_text(row.get("content",""))[:3500]
    lang = row.get("language") or detect_language_rule(content)
    cat = row.get("category") or detect_category_rule(row.get("title",""), row.get("heading",""), content)
    prompt = f"""
Create user-like FAQ for Enterprise RAG from this insurance website section.
Return JSON array only. 1-6 items.
Do not invent. Keep same language as content.

Item:
{{"question":"...","answer":"...","category":"{cat}","intent":"knowledge","confidence":0.8}}

Title:{row.get('title')}
Heading:{row.get('heading')}
Language:{lang}
Content:
{content}
"""
    try:
        return extract_json_array(call_ollama(prompt, num_predict=2200))
    except Exception:
        return []

def main():
    out = []
    rows = read_jsonl(INPUT)
    for i,r in enumerate(rows,1):
        print(f"[{i}/{len(rows)}] {r.get('heading')}")
        for item in gen(r):
            q,a = clean_text(item.get("question","")), clean_text(item.get("answer",""))
            if len(q) >= 5 and len(a) >= 10:
                out.append({"question":q,"answer":a,"category":item.get("category") or r.get("category"),"intent":item.get("intent","knowledge"),"confidence":item.get("confidence",0.8),"language":r.get("language"),"source_url":r.get("url"),"source_title":r.get("title"),"source_heading":r.get("heading")})
        time.sleep(0.2)
    write_jsonl(OUTPUT, out)
    print("DONE", len(out), OUTPUT)

if __name__ == "__main__":
    main()
