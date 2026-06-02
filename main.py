from pathlib import Path
import os
import sys

import requests as _requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from app.providers.ollama_provider import OllamaProvider, OllamaProviderError
from app.rag import retrieve, verify_grounding, get_active_flags

api = FastAPI(title="Enterprise RAG AI")
app = api  # uvicorn app:app

_STATIC_DIR = ROOT / "static"

# Serve JS/CSS with no-cache so browsers always pick up code changes
@app.get("/static/app.js")
def serve_app_js():
    path = _STATIC_DIR / "app.js"
    return FileResponse(str(path), media_type="application/javascript",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})

@app.get("/static/style.css")
def serve_style_css():
    path = _STATIC_DIR / "style.css"
    return FileResponse(str(path), media_type="text/css",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                                 "Pragma": "no-cache", "Expires": "0"})

if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


class ChatRequest(BaseModel):
    message: str
    company_code: str = ""


@app.get("/")
def index():
    index_file = ROOT / "static" / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"status": "ok", "service": "enterprise-rag-ai"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/rag/flags")
def rag_flags():
    """Show which RAG feature flags are currently active."""
    return get_active_flags()


_KB_LABELS: dict[str, str] = {
    "locktonwattana": "Lockton Wattana",
    "deves": "Deves Insurance",
    "mgcars": "MG Cars Thailand",
}


@app.get("/kb")
def list_kb():
    """Return available KB tenants with doc/faq counts.
    Falls back to companies table data when Supabase is slow/unavailable."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    hdr = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    default_code = os.getenv("COMPANY_CODE", "")

    # --- Try fast count query (3 s timeout) ---
    rows: list[dict] = []
    try:
        sql = """
            SELECT company_code,
                   (SELECT COUNT(*) FROM documents  d WHERE d.company_code = t.company_code) AS docs,
                   (SELECT COUNT(*) FROM faq_items  f WHERE f.company_code = t.company_code) AS faqs
            FROM (SELECT DISTINCT company_code FROM documents
                  UNION SELECT DISTINCT company_code FROM faq_items) t
            ORDER BY company_code;
        """
        r = _requests.post(f"{url}/pg/query", headers=hdr, json={"query": sql}, timeout=3)
        if r.ok:
            data = r.json()
            if isinstance(data, list):
                rows = data
    except Exception:
        pass  # fall through to companies-table fallback

    # --- Fallback: read companies table (also 3 s timeout) ---
    if not rows:
        try:
            r2 = _requests.post(
                f"{url}/pg/query", headers=hdr,
                json={"query": "SELECT company_code, company_name FROM companies WHERE is_active ORDER BY company_code;"},
                timeout=3,
            )
            if r2.ok:
                data2 = r2.json()
                if isinstance(data2, list):
                    rows = [{"company_code": row["company_code"], "docs": 0, "faqs": 0}
                            for row in data2]
        except Exception:
            pass

    # --- Last resort: hardcode known companies from env / _KB_LABELS ---
    if not rows:
        known = list(_KB_LABELS.keys())
        if default_code and default_code not in known:
            known.append(default_code)
        rows = [{"company_code": c, "docs": 0, "faqs": 0} for c in known]

    return {
        "default": default_code,
        "items": [
            {
                "code": row["company_code"],
                "label": _KB_LABELS.get(row["company_code"], row["company_code"]),
                "docs": int(row.get("docs") or 0),
                "faqs": int(row.get("faqs") or 0),
            }
            for row in rows
        ],
    }


@app.get("/provider")
def provider():
    p = OllamaProvider()
    return {
        "provider": p.config.provider,
        "base_url": p.config.base_url,
        "chat_model": p.config.chat_model,
        "generate_model": p.config.generate_model,
        "embed_model": p.config.embed_model,
    }


_COMPANY_HINTS: dict[str, str] = {
    "mgcars": (
        "MG Cars Thailand ไม่มีสำนักงานใหญ่เดียว แต่มีโชว์รูมและตัวแทนจำหน่ายทั่วประเทศ "
        "หากถูกถามเรื่องที่อยู่หรือสถานที่ตั้ง ให้แนะนำให้ลูกค้าค้นหาโชว์รูมใกล้บ้านได้ที่ "
        "https://www.mgcars.com/th/find-showroom "
        "สำหรับข้อมูลติดต่อบริษัท ดูได้ที่เว็บไซต์หลัก https://www.mgcars.com "
    ),
}


def _build_system_prompt(company_code: str) -> str:
    label = _KB_LABELS.get(company_code, company_code or "บริษัท")
    hint = _COMPANY_HINTS.get(company_code, "")
    return (
        f"คุณเป็นผู้ช่วยตอบคำถามของ {label} "
        f"(company_code: {company_code}) "
        "ตอบโดยอิงจากข้อมูลบริบทที่ให้มาเท่านั้น "
        "เมื่อถูกถามเรื่องชื่อบริษัท ที่อยู่ เบอร์โทร หรือข้อมูลติดต่อ ให้ใช้ข้อมูลจากบริบทด้านล่างได้เลย "
        + (f"{hint}" if hint else "")
        + "หากข้อมูลในบริบทไม่เพียงพอ ให้ตอบตรงๆ ว่าไม่มีข้อมูลนั้นในระบบและแนะนำช่องทางที่เกี่ยวข้อง "
        "ตอบเป็นภาษาเดียวกับคำถาม"
    )


def _build_sources(docs: list[dict], faqs: list[dict]) -> list[dict]:
    seen: set[str] = set()
    sources: list[dict] = []

    for d in docs:
        url = (d.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append({"url": url, "title": url, "similarity": round(float(d.get("similarity", 0)), 3)})

    for f in faqs:
        url = (f.get("source_url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append({"url": url, "title": url, "similarity": round(float(f.get("similarity", 0)), 3)})

    sources.sort(key=lambda s: s["similarity"], reverse=True)
    return sources[:5]


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        p = OllamaProvider()
        context, docs, faqs = retrieve(req.message, p, company_code=req.company_code)

        resolved_code = req.company_code or os.getenv("COMPANY_CODE", "")
        system_prompt = _build_system_prompt(resolved_code)

        if context:
            system = f"{system_prompt}\n\n{context}"
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": req.message},
            ]
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message},
            ]

        answer = p.chat(messages)
        answer = verify_grounding(req.message, answer, context, p)
        sources = _build_sources(docs, faqs)
        return {"answer": answer, "sources": sources}
    except OllamaProviderError as ex:
        raise HTTPException(status_code=500, detail=str(ex))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=False)
