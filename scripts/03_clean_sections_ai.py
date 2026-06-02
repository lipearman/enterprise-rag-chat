from _common import CRAWL_DIR, clean_text, read_jsonl, write_jsonl, call_ollama, extract_json_object, detect_language_rule, detect_category_rule
import json, time

INPUT = f"{CRAWL_DIR}/all_sections.jsonl"
OUTPUT = f"{CRAWL_DIR}/clean_sections.jsonl"
REPORT = f"{CRAWL_DIR}/clean_sections_report.json"
MAX_TEXT = 3500

def ai_clean(row):
    title, heading, content = row.get("title",""), row.get("heading",""), clean_text(row.get("content",""))[:MAX_TEXT]
    prompt = f"""
คุณคือระบบทำความสะอาดข้อมูลสำหรับ Enterprise RAG
ตอบเป็น JSON เท่านั้น:
{{"clean_content":"...", "language":"th/en", "category":"...", "page_type":"knowledge/contact/about/news/service/faq/general", "quality_score":0.0}}

ข้อกำหนด:
- ลบเมนู footer navigation cookie ข้อความซ้ำ
- ห้ามสรุปจนข้อมูลหาย
- ห้ามแต่งข้อมูลใหม่
- ถ้าเนื้อหาไม่มีสาระ ให้ clean_content เป็น ""

Title: {title}
Heading: {heading}
Content:
{content}
"""
    try:
        data = extract_json_object(call_ollama(prompt, num_predict=1800))
        if not data: raise Exception("no json")
        cc = clean_text(data.get("clean_content",""))
        return {
            **row,
            "content": cc,
            "language": data.get("language") or detect_language_rule(cc),
            "category": data.get("category") or detect_category_rule(title, heading, cc),
            "page_type": data.get("page_type") or "general",
            "quality_score": data.get("quality_score", 0.7)
        }, True
    except Exception:
        c = clean_text(row.get("content",""))
        return {**row, "content": c, "language": detect_language_rule(c), "category": detect_category_rule(title, heading, c), "page_type":"general", "quality_score":0.5}, False

def main():
    rows = read_jsonl(INPUT)
    out, ai_ok, ai_fail = [], 0, 0
    for i,r in enumerate(rows,1):
        print(f"[{i}/{len(rows)}] {r.get('heading')}")
        item, ok = ai_clean(r)
        if ok: ai_ok += 1
        else: ai_fail += 1
        if len(clean_text(item.get("content",""))) >= 80:
            out.append(item)
        time.sleep(0.2)
    write_jsonl(OUTPUT, out)
    report = {"input":INPUT,"output":OUTPUT,"rows":len(rows),"saved":len(out),"ai_ok":ai_ok,"ai_fail":ai_fail}
    open(REPORT,"w",encoding="utf-8").write(json.dumps(report,ensure_ascii=False,indent=2))
    print("DONE", report)

if __name__ == "__main__":
    main()
