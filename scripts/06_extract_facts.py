from _common import CRAWL_DIR, clean_text, read_jsonl, write_jsonl, call_ollama, extract_json_array, detect_language_rule
import re, time

INPUT = f"{CRAWL_DIR}/clean_sections.jsonl"
FACTS = f"{CRAWL_DIR}/facts.jsonl"
STAFF = f"{CRAWL_DIR}/staff.jsonl"

PHONE = re.compile(r"(?:\+66|0)[0-9\-\s]{7,20}")
EMAIL = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")

def ai_extract(row):
    content = clean_text(row.get("content",""))[:3000]
    prompt = f"""
Extract enterprise facts from insurance website content.
Return JSON array only.
Allowed item types:
company_name, phone, email, address, website, staff

Each item:
{{"type":"phone","value":"...","name":"...","position":"...","department":"...","confidence":0.8}}

Do not invent.

Title:{row.get('title')}
Heading:{row.get('heading')}
URL:{row.get('url')}
Content:
{content}
"""
    try:
        return extract_json_array(call_ollama(prompt, num_predict=1400))
    except Exception:
        return []

def main():
    rows = read_jsonl(INPUT)
    facts, staff, seen = [], [], set()
    for i,r in enumerate(rows,1):
        print(f"[{i}/{len(rows)}] {r.get('heading')}")
        text = f"{r.get('title','')}\n{r.get('heading','')}\n{r.get('content','')}"
        lang = r.get("language") or detect_language_rule(text)
        for p in PHONE.findall(text):
            k=("phone",clean_text(p))
            if k not in seen: seen.add(k); facts.append({"fact_type":"phone","fact_value":k[1],"language":lang,"source_url":r.get("url"),"confidence":0.8})
        for e in EMAIL.findall(text):
            k=("email",e)
            if k not in seen: seen.add(k); facts.append({"fact_type":"email","fact_value":e,"language":lang,"source_url":r.get("url"),"confidence":0.8})
        for item in ai_extract(r):
            typ = item.get("type")
            if typ == "staff":
                staff.append({"name":item.get("name") or item.get("value"),"position":item.get("position"),"department":item.get("department"),"email":item.get("email"),"phone":item.get("phone"),"language":lang,"source_url":r.get("url"),"confidence":item.get("confidence",0.8)})
            elif typ and item.get("value"):
                k=(typ, clean_text(item["value"]))
                if k not in seen: seen.add(k); facts.append({"fact_type":typ,"fact_value":k[1],"language":lang,"source_url":r.get("url"),"confidence":item.get("confidence",0.8)})
        time.sleep(0.2)
    write_jsonl(FACTS, facts); write_jsonl(STAFF, staff)
    print("DONE facts", len(facts), "staff", len(staff))

if __name__ == "__main__":
    main()
