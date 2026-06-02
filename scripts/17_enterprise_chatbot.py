from _common import get_embedding, call_ollama, clean_text
from intent_router import detect_intent
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client
import os, sys, json

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

FAQ_THRESHOLD = 0.50
TOP_K = 8

def rewrite(question):
    try:
        import importlib.util
        p = Path(__file__).resolve().parent / "13_query_rewrite.py"
        spec = importlib.util.spec_from_file_location("qr", p)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod.rewrite_query(question)
    except Exception:
        return question

def search_faq(question):
    emb = get_embedding(rewrite(question), 1200)
    res = supabase.rpc("match_faq", {"query_embedding": emb, "match_count": 5}).execute()
    return res.data or []

def search_docs(question):
    emb = get_embedding(rewrite(question), 1200)
    res = supabase.rpc("match_documents", {"query_embedding": emb, "match_count": TOP_K, "filter": {}}).execute()
    return res.data or []

def search_facts(question):
    q = question.lower()
    ft = None
    if any(k in q for k in ["โทร","phone","tel"]): ft = "phone"
    elif any(k in q for k in ["email","อีเมล"]): ft = "email"
    elif any(k in q for k in ["ที่อยู่","address"]): ft = "address"
    elif any(k in q for k in ["ชื่อบริษัท","company"]): ft = "company_name"
    query = supabase.table("company_facts").select("*")
    if ft: query = query.eq("fact_type", ft)
    return query.limit(20).execute().data or []

def search_staff(question):
    return supabase.table("staff_contacts").select("*").limit(30).execute().data or []

def build_context(kind, rows):
    if kind == "faq":
        return "\n\n".join([f"FAQ\nQ:{r.get('question')}\nA:{r.get('answer')}\nSource:{r.get('source_url')}\nSimilarity:{r.get('similarity')}" for r in rows])
    if kind == "fact":
        return "\n".join([f"{r.get('fact_type')}: {r.get('fact_value')} Source:{r.get('source_url')}" for r in rows])
    if kind == "staff":
        return "\n".join([f"Name:{r.get('name')} Position:{r.get('position')} Department:{r.get('department')} Email:{r.get('email')} Phone:{r.get('phone')} Source:{r.get('source_url')}" for r in rows])
    return "\n\n".join([f"Title:{r.get('title')}\nHeading:{r.get('heading')}\nURL:{r.get('url')}\nContent:{r.get('content')}" for r in rows])

def answer(question):
    intent = detect_intent(question, use_ai=True)
    print("INTENT:", intent)
    if intent == "fact":
        rows = search_facts(question)
        if rows: return generate(question, "fact", build_context("fact", rows))
    if intent == "staff":
        rows = search_staff(question)
        if rows: return generate(question, "staff", build_context("staff", rows))
    faq = search_faq(question)
    good = [r for r in faq if float(r.get("similarity") or 0) >= FAQ_THRESHOLD]
    if good:
        return generate(question, "faq", build_context("faq", good))
    docs = search_docs(question)
    # optional AI rerank
    try:
        import importlib.util
        p = Path(__file__).resolve().parent / "14_reranker.py"
        spec = importlib.util.spec_from_file_location("rr", p)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        docs = mod.rerank(question, docs, TOP_K)
    except Exception:
        pass
    return generate(question, "documents", build_context("documents", docs))

def generate(question, intent, context):
    prompt = f"""
คุณคือ Enterprise RAG Assistant สำหรับบริษัทนายหน้าประกันภัย
ตอบจาก Context เท่านั้น ห้ามเดา ถ้าไม่พบข้อมูลให้ตอบว่าไม่พบข้อมูลเพียงพอจากเอกสารที่มี
ตอบเป็นภาษาเดียวกับคำถาม เป็นธรรมชาติ และใส่ source ถ้ามี

Intent:{intent}
Context:
{context}

Question:{question}
Answer:
"""
    ans = call_ollama(prompt, num_predict=1200, temperature=0.1)
    try:
        import importlib.util
        p = Path(__file__).resolve().parent / "15_grounding.py"
        spec = importlib.util.spec_from_file_location("gr", p)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        g = mod.verify_grounding(question, ans, context)
        if not g.get("grounded", True) and g.get("fixed_answer"):
            return g["fixed_answer"]
    except Exception:
        pass
    return ans

if __name__ == "__main__":
    print("Enterprise RAG Chatbot ready. Type exit to quit.")
    while True:
        q = input("\nถามคำถาม: ").strip()
        if q.lower() in ["exit","quit","q"]: break
        try: print("\n" + answer(q))
        except Exception as e: print("ERROR:", e)
