import requests, math

URL = "http://llm-server:11434"

def embed(model, t):
    r = requests.post(f"{URL}/api/embed", json={"model": model, "input": t}, timeout=30)
    return r.json()["embeddings"][0]

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    na  = math.sqrt(sum(x*x for x in a))
    nb  = math.sqrt(sum(x*x for x in b))
    return dot / (na * nb)

q1 = "ประกันภัยรถยนต์ราคาเท่าไหร่"
q2 = "เบี้ยประกันสุขภาพ"
q3 = "motor insurance coverage"

print("=== mxbai-embed-large ===")
v1 = embed("mxbai-embed-large:latest", q1)
v2 = embed("mxbai-embed-large:latest", q2)
print(f"  dim: {len(v1)}")
tag = "BROKEN (identical)" if cosine(v1,v2) > 0.99 else "OK"
print(f"  TH1 vs TH2: {cosine(v1,v2):.4f}  => {tag}")

print()
print("=== bge-m3 ===")
b1 = embed("bge-m3:latest", q1)
b2 = embed("bge-m3:latest", q2)
b3 = embed("bge-m3:latest", q3)
print(f"  dim: {len(b1)}")
print(f"  TH1 vs TH2: {cosine(b1,b2):.4f}  (different Thai queries)")
print(f"  TH1 vs EN:  {cosine(b1,b3):.4f}  (cross-lingual motor insurance)")
print(f"  TH2 vs EN:  {cosine(b2,b3):.4f}  (cross-lingual health insurance)")
