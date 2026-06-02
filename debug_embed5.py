"""
Check bge-m3 Modelfile config and test nomic-embed-text as fallback.
"""
import os, requests, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
EMBED_URL = os.getenv("OLLAMA_EMBED_BASE_URL", "http://llm-server:11434")

def show_model(name):
    r = requests.post(f"{EMBED_URL}/api/show", json={"name": name}, timeout=10)
    return r.json()

def try_embed(model, text):
    try:
        r = requests.post(f"{EMBED_URL}/api/embed",
                          json={"model": model, "input": [text]},
                          timeout=30)
        r.raise_for_status()
        return True, len(r.json()["embeddings"][0])
    except Exception as e:
        return False, str(e)[:80]

# Check bge-m3 config
print("=== bge-m3:latest Modelfile ===")
info = show_model("bge-m3:latest")
mf = info.get("modelfile", "")
for line in mf.split("\n"):
    if line.strip():
        print(f"  {line}")
print(f"\nmodel_info: {json.dumps(info.get('model_info', {}), indent=2)[:500]}")

# Test text sizes
text_500  = "The quick brown fox jumps over the lazy dog. " * 11  # ~495 chars
text_1800 = "The quick brown fox jumps over the lazy dog. " * 40   # ~1800 chars
thai_500  = "การประกันภัยคุ้มครองความเสียหาย " * 15              # ~500 chars

print("\n=== bge-m3:latest embed tests ===")
for label, txt in [("500 chars English", text_500[:500]),
                   ("1800 chars English", text_1800[:1800]),
                   ("500 chars Thai", thai_500[:500])]:
    ok, res = try_embed("bge-m3:latest", txt)
    print(f"  {label:25s}: {'OK dim='+str(res) if ok else 'FAIL'}")

# Check nomic-embed-text
print("\n=== nomic-embed-text:latest Modelfile ===")
info2 = show_model("nomic-embed-text:latest")
mf2 = info2.get("modelfile", "")
for line in mf2.split("\n"):
    if line.strip():
        print(f"  {line}")

print("\n=== nomic-embed-text:latest embed tests ===")
for label, txt in [("200 chars English", text_500[:200]),
                   ("500 chars English", text_500[:500]),
                   ("1800 chars English", text_1800[:1800]),
                   ("500 chars Thai", thai_500[:500])]:
    ok, res = try_embed("nomic-embed-text:latest", txt)
    print(f"  {label:25s}: {'OK dim='+str(res) if ok else 'FAIL: '+str(res)}")
