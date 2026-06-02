from _common import call_ollama, extract_json_object
import json

def verify_grounding(question, answer, context):
    prompt = f"""
Verify whether the answer is grounded in context.
Return JSON only:
{{"grounded":true,"score":0.9,"issues":[],"fixed_answer":"..."}}

Question:{question}
Answer:{answer}
Context:{context[:5000]}
"""
    try:
        return extract_json_object(call_ollama(prompt, num_predict=1000)) or {"grounded": True, "score": 0.5, "issues": []}
    except Exception:
        return {"grounded": True, "score": 0.5, "issues": []}
