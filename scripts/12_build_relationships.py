from _common import CRAWL_DIR, read_jsonl, write_jsonl, call_ollama, extract_json_array, clean_text
import time

INPUT = f"{CRAWL_DIR}/knowledge_items.jsonl"
OUTPUT = f"{CRAWL_DIR}/relationships.jsonl"

def extract(row):
    prompt = f"""
Build relationship triples for insurance enterprise knowledge graph.
Return JSON array only.
Triple:
{{"subject":"Marine Insurance","predicate":"has_topic","object":"Cargo Insurance","subject_type":"service","object_type":"topic","confidence":0.8}}

Text:
Title:{row.get('title')}
Heading:{row.get('heading')}
Knowledge:{row.get('answer')}
"""
    try:
        return extract_json_array(call_ollama(prompt, num_predict=1200))
    except Exception:
        return []

def main():
    out = []
    for i,r in enumerate(read_jsonl(INPUT),1):
        print("[REL]", i)
        for item in extract(r):
            if item.get("subject") and item.get("object"):
                item["source_url"] = r.get("url")
                out.append(item)
        time.sleep(0.1)
    write_jsonl(OUTPUT,out)
    print("DONE", len(out))

if __name__ == "__main__":
    main()
