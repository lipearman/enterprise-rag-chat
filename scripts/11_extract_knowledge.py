from _common import CRAWL_DIR, read_jsonl, write_jsonl, call_ollama, extract_json_array, clean_text
import time

INPUT = f"{CRAWL_DIR}/chunks.jsonl"
OUTPUT = f"{CRAWL_DIR}/knowledge_items.jsonl"

def extract(row):
    prompt = f"""
Extract structured knowledge from insurance website content.
Return JSON array only.
Types: definition, coverage, exclusion, claim_process, benefit, requirement, contact_instruction, general_fact

Item:
{{"knowledge_type":"definition","question":"...","answer":"...","facts":["..."]}}

Title:{row.get('title')}
Heading:{row.get('heading')}
Content:
{clean_text(row.get('content',''))[:3000]}
"""
    try:
        return extract_json_array(call_ollama(prompt, num_predict=1800))
    except Exception:
        return []

def main():
    out = []
    rows = read_jsonl(INPUT)
    for i,r in enumerate(rows,1):
        print(f"[{i}/{len(rows)}]")
        for item in extract(r):
            if item.get("answer"):
                out.append({"source_id":r.get("id"),"url":r.get("url"),"title":r.get("title"),"heading":r.get("heading"),"language":r.get("language"),"category":r.get("category"),"knowledge_type":item.get("knowledge_type","general_fact"),"question":item.get("question"),"answer":item.get("answer"),"facts":item.get("facts",[])})
        time.sleep(0.15)
    write_jsonl(OUTPUT,out)
    print("DONE", len(out))

if __name__ == "__main__":
    main()
