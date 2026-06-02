import os, re, json, time, hashlib, math, requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

CRAWL_DIR = os.getenv("CRAWL_DIR", "/mnt/c/crawl-output/locktonwattana")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBED_BASE_URL = os.getenv("OLLAMA_EMBED_BASE_URL", OLLAMA_BASE_URL)
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:14b-instruct")
EMBED_MODEL = os.getenv("EMBED_MODEL", "mxbai-embed-large")
EMBED_DIMENSION = int(os.getenv("EMBED_DIMENSION", "1024"))

def ensure_dir():
    Path(CRAWL_DIR).mkdir(parents=True, exist_ok=True)

def clean_text(text):
    text = text or ""
    text = text.replace("\u0000", " ").replace("\ufeff", " ").replace("\u00a0", " ")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def detect_language_rule(text):
    return "th" if re.search(r"[\u0E00-\u0E7F]", text or "") else "en"

def detect_category_rule(title, heading, content):
    t = f"{title} {heading} {content}".lower()
    rules = [
        ("motor_insurance", ["motor", "car insurance", "รถยนต์", "ประกันรถ"]),
        ("marine_insurance", ["marine", "cargo", "ทางทะเล", "ขนส่ง"]),
        ("health_insurance", ["health", "medical", "สุขภาพ"]),
        ("property_insurance", ["property", "fire", "ทรัพย์สิน", "อัคคีภัย"]),
        ("liability_insurance", ["liability", "ความรับผิด"]),
        ("employee_benefits", ["employee", "benefit", "สวัสดิการ"]),
        ("claims", ["claim", "เคลม", "สินไหม"]),
        ("contact", ["contact", "ติดต่อ", "phone", "email", "ที่อยู่"]),
        ("about", ["about", "เกี่ยวกับ"]),
    ]
    for cat, keys in rules:
        if any(k in t for k in keys):
            return cat
    return "general"

def extract_json_object(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if m:
        try: return json.loads(m.group(0))
        except Exception: return None
    return None

def extract_json_array(text):
    try:
        data = json.loads(text)
        if isinstance(data, list): return data
        if isinstance(data, dict) and "items" in data: return data["items"]
    except Exception:
        pass
    m = re.search(r"\[\s*{.*}\s*\]", text or "", re.DOTALL)
    if m:
        try: return json.loads(m.group(0))
        except Exception: return []
    return []

def call_ollama(prompt, model=None, num_predict=1600, temperature=0.1, timeout=600):
    res = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": model or LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "top_p": 0.9, "num_predict": num_predict}
        },
        timeout=timeout
    )
    res.raise_for_status()
    return res.json().get("response", "").strip()

def _embed_raw(text, timeout=300):
    """Call Ollama embed endpoint. Returns embedding or raises on error."""
    res = requests.post(
        f"{EMBED_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=timeout
    )
    res.raise_for_status()
    data = res.json()
    if "embeddings" in data and data["embeddings"]:
        return data["embeddings"][0]
    return data.get("embedding")

def _valid_emb(e):
    """Check embedding has no NaN/Inf."""
    if not e: return False
    return not any((v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))) for v in e)

def get_embedding(text, max_len=1200):
    """Get embedding with chunk-averaging fallback for bge-m3 NaN bug."""
    text = clean_text(text)[:max_len]
    if not text:
        return None
    # First try the full text
    try:
        emb = _embed_raw(text)
        if _valid_emb(emb):
            return emb
    except Exception:
        pass
    # After a 500/NaN error, give the model time to recover before sub-chunking
    time.sleep(5)
    # Fallback: split into 150-char chunks, average valid embeddings
    chunk_size = 150
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size) if text[i:i+chunk_size].strip()]
    if not chunks:
        return None
    valid_embs = []
    for chunk in chunks:
        try:
            e = _embed_raw(chunk, timeout=120)
            if _valid_emb(e):
                valid_embs.append(e)
        except Exception:
            continue
    if not valid_embs:
        return None
    # Average all valid embeddings
    dim = len(valid_embs[0])
    avg = [sum(e[i] for e in valid_embs) / len(valid_embs) for i in range(dim)]
    return avg

def read_jsonl(path):
    rows = []
    if not os.path.exists(path): return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: rows.append(json.loads(line))
            except Exception: pass
    return rows

def write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def md5_id(*parts):
    raw = "|".join([str(p) for p in parts])
    return hashlib.md5(raw.encode("utf-8")).hexdigest()
