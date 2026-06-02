from _common import call_ollama, extract_json_object

FACT = ["ชื่อบริษัท","company","เบอร์","โทร","phone","tel","email","อีเมล","ที่อยู่","address","website","เว็บ"]
STAFF = ["ใครดูแล","ผู้ดูแล","เจ้าหน้าที่","contact person","ผู้ติดต่อ","ทีม","แผนก","manager","broker","consultant"]

def detect_intent_rule(question):
    q = question.lower()
    if any(k.lower() in q for k in STAFF): return "staff"
    if any(k.lower() in q for k in FACT): return "fact"
    return "knowledge"

def detect_intent_ai(question):
    prompt = f"""
Classify intent for enterprise insurance chatbot.
Return JSON only:
{{"intent":"fact/staff/faq/knowledge/claim/comparison","reason":"..."}}

Question:{question}
"""
    try:
        data = extract_json_object(call_ollama(prompt, num_predict=300))
        return data.get("intent") if data else detect_intent_rule(question)
    except Exception:
        return detect_intent_rule(question)

def detect_intent(question, use_ai=False):
    return detect_intent_ai(question) if use_ai else detect_intent_rule(question)
