# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"D:\MyWorkSpace\RAG\enterprise-rag")
os.chdir(r"D:\MyWorkSpace\RAG\enterprise-rag")
from dotenv import load_dotenv
load_dotenv(".env")

from app.rag import _detect_intent_rule, _fact_type_from_query, _search_company_facts, _search_staff_contacts

print("=== Intent Detection ===")
queries = [
    "ขอเบอร์โทรบริษัทหน่อย",
    "ที่อยู่บริษัทอยู่ที่ไหน",
    "email บริษัทคืออะไร",
    "ใครดูแลการเคลมประกัน",
    "ผู้ติดต่อฝ่ายประกัน",
    "marine insurance คุ้มครองอะไร",
    "ชื่อบริษัทเต็มๆ",
]
for q in queries:
    intent = _detect_intent_rule(q)
    ftype  = _fact_type_from_query(q)
    print(f"  [{intent:9s}] fact_type={str(ftype):12s}  '{q}'")

print("\n=== company_facts — phone query ===")
facts = _search_company_facts("ขอเบอร์โทรบริษัทหน่อย", "locktonwattana")
for f in facts:
    print(f"  [{f.get('fact_type'):15s}] {f.get('fact_value')}")

print("\n=== company_facts — address query ===")
facts2 = _search_company_facts("ที่อยู่บริษัทอยู่ที่ไหน", "locktonwattana")
for f in facts2:
    print(f"  [{f.get('fact_type'):15s}] {f.get('fact_value')}")

print("\n=== staff_contacts ===")
staff = _search_staff_contacts("ใครดูแลการเคลม", "locktonwattana")
for s in staff[:5]:
    print(f"  {s.get('name')} | {s.get('position')} | {s.get('phone') or s.get('email')}")
