from _common import call_ollama, extract_json_array, clean_text
import json

def rerank(question, candidates, top_k=8):
    prompt = f"""
Rerank contexts for answering the question. Return JSON array only:
[{{"index":1,"score":0.95,"reason":"..."}}]

Question:
{question}

Candidates:
{json.dumps([{"index":i+1,"title":c.get("title"),"heading":c.get("heading"),"content":clean_text(c.get("content",""))[:800]} for i,c in enumerate(candidates)], ensure_ascii=False)}
"""
    try:
        ranks = extract_json_array(call_ollama(prompt, num_predict=1200))
        order = []
        for r in ranks:
            idx = int(r.get("index",0)) - 1
            if 0 <= idx < len(candidates):
                c = candidates[idx]
                c["_rerank_score"] = float(r.get("score",0))
                c["_rerank_reason"] = r.get("reason","")
                order.append(c)
        return order[:top_k] if order else candidates[:top_k]
    except Exception:
        return candidates[:top_k]
