"""
Test hypotheses for why bge-m3 500s after ~257 chars.
"""
import os, requests, time
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent / ".env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBED_URL    = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")
EMBED_MODEL  = os.getenv("EMBED_MODEL", "bge-m3:latest")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def try_embed(text, label=""):
    try:
        r = requests.post(f"{EMBED_URL}/api/embed",
                          json={"model": EMBED_MODEL, "input": [text]},
                          timeout=30)
        r.raise_for_status()
        return True, len(r.json()["embeddings"][0])
    except Exception as e:
        return False, str(e)

# Get the failing row
resp = supabase.table("documents").select("id,text_for_embedding").range(834, 834).execute()
raw = (resp.data[0].get("text_for_embedding") or "").replace("\x00", "")

print(f"Text length: {len(raw)}")
print(f"Text [{256}:{270}]: {repr(raw[256:270])}")
print()

# H1: Is it the U+2019 at position 80 causing delayed tokenizer failure?
clean = raw.replace("’", "'")  # replace curly apostrophe with straight
ok, res = try_embed(clean[:500])
print(f"H1 - straight apostrophe (500 chars): {'OK' if ok else 'FAIL'} | {res}")

ok, res = try_embed(clean[:873])
print(f"H1 - straight apostrophe (full text): {'OK' if ok else 'FAIL'} | {res}")
time.sleep(0.5)

# H2: Is it specific text content at 257-500?
pure_ascii_300 = "A" * 300
ok, res = try_embed(pure_ascii_300)
print(f"\nH2 - pure ASCII 300 chars: {'OK' if ok else 'FAIL'} | {res}")

pure_ascii_900 = "The quick brown fox jumps over the lazy dog. " * 20  # 900 chars
ok, res = try_embed(pure_ascii_900)
print(f"H2 - repeated English 900 chars: {'OK' if ok else 'FAIL'} | {res}")
time.sleep(0.5)

# H3: Thai text causes tokenizer overflow?
thai_900 = "การประกันภัยรถยนต์คุ้มครองความเสียหายที่เกิดขึ้นกับรถของคุณ " * 15
ok, res = try_embed(thai_900)
print(f"\nH3 - Thai text 900 chars: {'OK' if ok else 'FAIL'} | {res}")
time.sleep(0.5)

# H4: The \n or specific phrases cause issue? Check chars 200-270 carefully
segment = raw[200:270]
print(f"\nH4 - raw segment [200:270]: {repr(segment)}")
ok, res = try_embed(segment)
print(f"H4 - embed segment alone: {'OK' if ok else 'FAIL'} | {res}")

# H5: Is it a rate-limit / server busy issue? Wait and retry
time.sleep(2)
ok, res = try_embed(raw[:500])
print(f"\nH5 - retry after 2s (500 chars): {'OK' if ok else 'FAIL'} | {res}")

time.sleep(5)
ok, res = try_embed(raw[:500])
print(f"H5 - retry after 5s (500 chars): {'OK' if ok else 'FAIL'} | {res}")
