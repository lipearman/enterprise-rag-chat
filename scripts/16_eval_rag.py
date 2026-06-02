from _common import CRAWL_DIR, call_ollama, extract_json_object
from pathlib import Path
import json, time, subprocess, sys

TESTS = [
    "ชื่อบริษัทอะไร",
    "ที่อยู่บริษัทอยู่ที่ไหน",
    "เบอร์โทรบริษัทคืออะไร",
    "ประกันรถยนต์มีกี่ประเภท",
    "Marine insurance คืออะไร",
]

REPORT = f"{CRAWL_DIR}/rag_eval_report.json"

def eval_answer(q, answer):
    prompt = f"""
Evaluate RAG answer quality. Return JSON only:
{{"score":0.0,"relevance":0.0,"grounded":0.0,"naturalness":0.0,"comment":"..."}}

Question:{q}
Answer:{answer}
"""
    try:
        return extract_json_object(call_ollama(prompt, num_predict=700)) or {}
    except Exception:
        return {}

def main():
    # This script assumes 17_enterprise_chatbot.py is used manually.
    # For now it creates an evaluation template.
    rows = [{"question": q, "expected_check": "manual", "status": "pending"} for q in TESTS]
    Path(REPORT).write_text(json.dumps({"tests":rows,"created_at":time.strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Created eval template:", REPORT)

if __name__ == "__main__":
    main()
