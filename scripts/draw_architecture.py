"""
Enterprise RAG — Clean Architecture Diagram  (architecture.jpg)
Canvas : 28 × 20 inches @ 150 dpi
Layout : Pipeline (left) | Data Store (centre) | AI Servers (right)
         Production bar (bottom, full-width)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ── palette ───────────────────────────────────────────────────────────────────
BG    = "#0f172a"
PANEL = "#1e293b"
MUTED = "#94a3b8"
TEXT  = "#e2e8f0"

BLUE   = "#38bdf8"
GREEN  = "#34d399"
PURPLE = "#a78bfa"
ORANGE = "#fb923c"
YELLOW = "#fbbf24"
PINK   = "#f472b6"
RED    = "#fb7185"
SLATE  = "#475569"

# ── canvas ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(28, 20))
ax.set_xlim(0, 28); ax.set_ylim(0, 20)
ax.axis("off")
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# ═════════════════════════════════════════════════════════════════════════════
# helpers
# ═════════════════════════════════════════════════════════════════════════════
def rbox(x, y, w, h, fc, ec, alpha=0.20, lw=1.6, radius=0.25, zorder=3):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.0,rounding_size={radius}",
                       facecolor=fc, alpha=alpha,
                       edgecolor=ec, linewidth=lw, zorder=zorder)
    ax.add_patch(p)

def txt(x, y, s, color=TEXT, size=10, bold=False, ha="center", va="center", zorder=6):
    ax.text(x, y, s, color=color, fontsize=size,
            fontweight="bold" if bold else "normal",
            ha=ha, va=va, zorder=zorder, fontfamily="DejaVu Sans")

def arr(x1, y1, x2, y2, color=SLATE, lw=1.8, rad=0.0, both=False):
    style = "<|-|>" if both else "-|>"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                mutation_scale=14,
                                connectionstyle=f"arc3,rad={rad}"),
                zorder=5)

def hline(x1, x2, y, color=SLATE, lw=1.4, dash=(5,3)):
    ax.plot([x1, x2], [y, y], color=color, lw=lw,
            linestyle=(0, dash), zorder=4)

# ═════════════════════════════════════════════════════════════════════════════
# 0.  TITLE
# ═════════════════════════════════════════════════════════════════════════════
rbox(0.3, 19.1, 27.4, 0.75, BLUE, BLUE, alpha=0.12, lw=1.2)
txt(14.0, 19.55, "Enterprise RAG — System Architecture",
    color=BLUE,  size=20, bold=True)
txt(14.0, 19.22, "MG Cars Thailand  |  Multi-tenant Knowledge Base Chatbot",
    color=MUTED, size=11)

# ═════════════════════════════════════════════════════════════════════════════
# 1.  ZONE BACKGROUNDS
# ═════════════════════════════════════════════════════════════════════════════
# Zone A  —  KB Build Pipeline (left)
rbox(0.3, 6.3, 7.6, 12.55, PURPLE, "#5b4fa0", alpha=0.07, lw=1.2, radius=0.4)
# Zone B  —  Data Store (centre)
rbox(8.3, 6.3, 9.8, 12.55, GREEN,  "#2f6b50", alpha=0.07, lw=1.2, radius=0.4)
# Zone C  —  AI Servers (right)
rbox(18.4, 9.1, 9.3, 9.75, ORANGE, "#7a4820", alpha=0.07, lw=1.2, radius=0.4)
# Zone D  —  Production (bottom full-width)
rbox(0.3,  0.3, 27.4, 5.75, BLUE, "#1e5f7a", alpha=0.07, lw=1.2, radius=0.4)

# Zone labels
txt(4.1,  18.62, "Zone A  —  KB Build Pipeline  ( scripts/ )",       PURPLE, 12, bold=True)
txt(13.2, 18.62, "Zone B  —  Data Store  ( Supabase / PostgreSQL + pgvector )", GREEN, 12, bold=True)
txt(23.05,18.62, "Zone C  —  AI Servers",                             ORANGE, 12, bold=True)
txt(14.0,  5.85, "Zone D  —  Production  ( API Server + Browser UI )",BLUE,  12, bold=True)

# ═════════════════════════════════════════════════════════════════════════════
# 2.  KB BUILD PIPELINE  —  9 steps, vertical, left column
# ═════════════════════════════════════════════════════════════════════════════
STEPS = [
    # (label-line1,          label-line2,              color,  tag)
    ("01  Crawl Website",   "aiohttp + BeautifulSoup", BLUE,   "WEB"),
    ("02  Extract Sections","HTML  →  structured chunks", BLUE,  "CUT"),
    ("03  Clean  (AI)",     "LLM remove noise / boilerplate", PURPLE, "AI"),
    ("04  Semantic Chunk (AI)","LLM split content by topic",  PURPLE, "AI"),
    ("05  Embed Documents", "bge-m3  →  vector(1024)",  GREEN,  "VEC"),
    ("06  Extract Facts (AI)","company_name / address / phone", PURPLE,"AI"),
    ("07  Import Facts",    "→  company_facts  /  staff_contacts", GREEN, "DB"),
    ("08  Generate FAQ (AI)","LLM  →  Q&A pairs",       PURPLE, "AI"),
    ("09  Embed FAQ",       "bge-m3  →  vector(1024)",  GREEN,  "VEC"),
]

SX, SW, SH, SGAP = 0.55, 7.1, 0.95, 0.22
S_TOP = 18.0

for i, (l1, l2, col, tag) in enumerate(STEPS):
    sy = S_TOP - i * (SH + SGAP)
    # box
    rbox(SX, sy - SH, SW, SH, col, col, alpha=0.20, lw=1.4)
    # step number circle
    circ = plt.Circle((SX + 0.38, sy - SH/2), 0.27,
                       color=col, alpha=0.30, zorder=5)
    ax.add_patch(circ)
    txt(SX + 0.38, sy - SH/2, str(i+1), col, size=9, bold=True)
    # tag badge
    rbox(SX + 0.78, sy - SH + 0.18, 0.72, 0.42,
         col, col, alpha=0.35, lw=1, radius=0.12, zorder=6)
    txt(SX + 1.14, sy - SH + 0.39, tag, col, size=7.5, bold=True)
    # text
    txt(SX + 1.85, sy - SH/2 + 0.18, l1, col,   size=10, bold=True, ha="left")
    txt(SX + 1.85, sy - SH/2 - 0.18, l2, MUTED, size=8.8, ha="left")
    # connector arrow to next step
    if i < len(STEPS) - 1:
        arr(SX + SW/2, sy - SH, SX + SW/2, sy - SH - SGAP + 0.04,
            color=SLATE, lw=1.4)

# ═════════════════════════════════════════════════════════════════════════════
# 3.  DATA STORE — Supabase tables
# ═════════════════════════════════════════════════════════════════════════════
TABLES = [
    # (name,            description,                      color)
    ("documents",      "vector(1024)  •  company_code  •  content", BLUE),
    ("faq_items",      "vector(1024)  •  company_code  •  Q & A",   BLUE),
    ("company_facts",  "fact_type  •  fact_value  •  confidence",    YELLOW),
    ("staff_contacts", "name  •  email  •  phone  •  department",    YELLOW),
    ("companies",      "company_code  •  company_name  •  base_url", GREEN),
    ("metadata_items", "keywords  •  intent_tags  •  category",      MUTED),
    ("knowledge_items","question  •  answer  •  knowledge_type",     MUTED),
    ("relationships",  "subject  →  predicate  →  object",           MUTED),
]

TX, TW, TH, TGAP = 8.55, 9.3, 0.88, 0.20
T_TOP = 18.0

for i, (tname, tdesc, tcol) in enumerate(TABLES):
    ty = T_TOP - i * (TH + TGAP)
    rbox(TX, ty - TH, TW, TH, tcol, tcol, alpha=0.20, lw=1.4)
    # table icon bar
    rbox(TX + 0.15, ty - TH + 0.12, 0.28, TH - 0.24,
         tcol, tcol, alpha=0.50, lw=0, radius=0.08, zorder=5)
    txt(TX + 1.1, ty - TH/2 + 0.20, tname, tcol,   size=10.5, bold=True, ha="left")
    txt(TX + 1.1, ty - TH/2 - 0.18, tdesc, MUTED,  size=8.8,  ha="left")

# IVFFlat index badge (floats near documents/faq rows)
rbox(14.2, 15.80, 3.3, 0.50, BLUE, BLUE, alpha=0.30, lw=1.1, radius=0.15)
txt(15.85, 16.05, "IVFFlat index  (cosine, lists=100)", BLUE, size=8.5, bold=True)

# pgvector & RPC badges (bottom of DB zone)
rbox(8.55,  6.55, 2.6, 0.48, GREEN,  GREEN,  alpha=0.30, lw=1.1, radius=0.15)
txt(9.85,   6.79, "pgvector  ext.", GREEN, size=8.5, bold=True)

rbox(11.45, 6.55, 6.4, 0.48, PURPLE, PURPLE, alpha=0.30, lw=1.1, radius=0.15)
txt(14.65,  6.79, "RPC :  match_documents  •  match_faq", PURPLE, size=8.5, bold=True)

# ═════════════════════════════════════════════════════════════════════════════
# 4.  AI SERVERS  (right zone)
# ═════════════════════════════════════════════════════════════════════════════
# — Ollama Cloud ——————————————————————————
rbox(18.6, 15.0, 8.8, 3.4, ORANGE, ORANGE, alpha=0.22, lw=1.6, radius=0.35)
txt(23.0, 18.10, "Ollama Cloud", ORANGE, size=14, bold=True)
txt(23.0, 17.62, "https://ollama.com", MUTED, size=10)

rbox(19.0, 14.95, 3.9, 0.62, ORANGE, ORANGE, alpha=0.30, lw=1, radius=0.15)
txt(20.95, 15.26, "Chat  /  Generate", ORANGE, size=9.5, bold=True)
rbox(23.2, 14.95, 3.9, 0.62, YELLOW, YELLOW, alpha=0.30, lw=1, radius=0.15)
txt(25.15, 15.26, "qwen2.5:14b-instruct", YELLOW, size=9.5, bold=True)

# — llm-server (Local Ollama) ————————————
rbox(18.6,  9.3, 8.8, 5.4, GREEN, GREEN, alpha=0.22, lw=1.6, radius=0.35)
txt(23.0, 14.40, "llm-server  ( Local Ollama )", GREEN, size=14, bold=True)
txt(23.0, 13.90, "http://llm-server:11434", MUTED, size=10)

# embed model sub-box
rbox(19.0, 12.85, 8.0, 0.80, BLUE, BLUE, alpha=0.25, lw=1.1, radius=0.2)
txt(23.0, 13.25, "Embedding Model  —  bge-m3:latest  →  vector(1024)", BLUE, size=10, bold=True)

# also hosts Supabase
rbox(19.0, 11.75, 8.0, 0.80, GREEN, GREEN, alpha=0.25, lw=1.1, radius=0.2)
txt(23.0, 12.15, "Supabase  (PostgreSQL + pgvector)  :8000", GREEN, size=10, bold=True)

# LLM fallback note
rbox(19.0, 10.65, 8.0, 0.80, PURPLE, PURPLE, alpha=0.25, lw=1.1, radius=0.2)
txt(23.0, 11.05, "LLM fallback  —  qwen2.5:14b-instruct  :11434", PURPLE, size=10, bold=True)

txt(23.0, 10.10, "Tailscale VPN  —  100.99.80.84", MUTED, size=9)
txt(23.0,  9.65, "llm-server.tail923b9a.ts.net", MUTED, size=9)

# ═════════════════════════════════════════════════════════════════════════════
# 5.  PRODUCTION BAR  (bottom)
# ═════════════════════════════════════════════════════════════════════════════
# — FastAPI ————————————————————————————————
rbox(0.55, 0.55, 8.4, 5.0, BLUE, BLUE, alpha=0.22, lw=1.6, radius=0.35)
txt(4.75, 5.22, "FastAPI   ( main.py )", BLUE, size=14, bold=True)
txt(4.75, 4.72, "uvicorn  •  host 0.0.0.0 : 8080", MUTED, size=10)

endpoints = [
    ("POST /chat",         "send message, get answer"),
    ("GET  /kb",           "list KB tenants + doc counts"),
    ("GET  /provider",     "show LLM provider info"),
    ("GET  /rag/flags",    "show active feature flags"),
    ("GET  /static/*",     "serve UI files (no-cache)"),
]
for j, (ep, desc) in enumerate(endpoints):
    ey = 4.10 - j * 0.60
    rbox(0.85, ey - 0.22, 7.9, 0.46, BLUE, BLUE, alpha=0.15, lw=0.8, radius=0.12)
    txt(1.15, ey, ep,   BLUE, size=9.5, bold=True, ha="left")
    txt(5.05, ey, desc, MUTED, size=9,  ha="left")

# — RAG Pipeline ——————————————————————————
rbox(9.3, 0.55, 9.0, 5.0, PURPLE, PURPLE, alpha=0.22, lw=1.6, radius=0.35)
txt(13.8, 5.22, "RAG Pipeline   ( app/rag.py )", PURPLE, size=14, bold=True)

rag_steps = [
    ("1", "Intent Detection",    "rule-based: fact / staff / knowledge / claim",  YELLOW),
    ("2", "Embed Query",         "bge-m3  •  chunk-avg fallback for NaN bug",     BLUE),
    ("3", "Vector Search",       "match_documents  +  match_faq  (similarity >= 0.40)", GREEN),
    ("4", "Search company_facts","phone / address / website facts (pg/query)",    YELLOW),
    ("5", "Rerank  +  Context",  "optional AI rerank  →  build context string",   PURPLE),
    ("6", "LLM Answer",          "Ollama Chat  →  optional Grounding verify",     ORANGE),
]
for j, (num, step, desc, col) in enumerate(rag_steps):
    ry = 4.55 - j * 0.63
    rbox(9.55, ry - 0.27, 8.4, 0.52, col, col, alpha=0.18, lw=1, radius=0.15)
    # circle number
    circ2 = plt.Circle((9.92, ry), 0.20, color=col, alpha=0.40, zorder=6)
    ax.add_patch(circ2)
    txt(9.92, ry, num, col, size=9, bold=True)
    txt(10.22, ry + 0.07, step, col,  size=9.5, bold=True, ha="left")
    txt(10.22, ry - 0.16, desc, MUTED, size=8.0, ha="left")

# — Browser UI —————————————————————————————
rbox(18.6, 0.55, 9.1, 5.0, PINK, PINK, alpha=0.22, lw=1.6, radius=0.35)
txt(23.15, 5.22, "Browser UI   ( static/ )", PINK, size=14, bold=True)

ui_items = [
    ("index.html",  "app shell, mobile-responsive layout"),
    ("app.js",      "chat logic, KB selector, history (localStorage v3)"),
    ("style.css",   "dark theme, dvh layout, safe-area iOS fix"),
    ("Features :",  "sources persist on refresh  •  KB switcher"),
    ("Mobile :",    "100dvh  •  env(safe-area-inset-bottom)"),
]
for j, (k, v) in enumerate(ui_items):
    uy = 4.50 - j * 0.68
    rbox(18.9, uy - 0.28, 8.5, 0.53, PINK, PINK, alpha=0.15, lw=0.8, radius=0.12)
    txt(19.2, uy, k, PINK,  size=9.5, bold=True, ha="left")
    txt(21.35, uy, v, MUTED, size=9.0, ha="left")

# ═════════════════════════════════════════════════════════════════════════════
# 6.  ARROWS  —  data flows
# ═════════════════════════════════════════════════════════════════════════════

# — Build-time: Pipeline → Supabase tables ————————————————————————————————
# step 05 (embed docs) → documents table
arr(7.65, 18.0 - 4*(0.95+0.22) - 0.475,   # mid of step 05
    8.55, 18.0 - 0*(0.88+0.20) - 0.44,     # documents row mid
    color=BLUE, lw=1.6, rad=-0.25)

# step 07 (import facts) → company_facts
arr(7.65, 18.0 - 6*(0.95+0.22) - 0.475,
    8.55, 18.0 - 2*(0.88+0.20) - 0.44,
    color=YELLOW, lw=1.6, rad=-0.18)

# step 09 (embed FAQ) → faq_items
arr(7.65, 18.0 - 8*(0.95+0.22) - 0.475,
    8.55, 18.0 - 1*(0.88+0.20) - 0.44,
    color=GREEN, lw=1.6, rad=0.30)

# — Build-time: Pipeline embed steps → llm-server (embed) ————————————————
# one representative arrow from step 05
arr(7.65, 18.0 - 4*(0.95+0.22) - 0.475,
    18.6, 13.25,
    color=GREEN, lw=1.8, rad=-0.20)

# label on that arrow
ax.text(13.8, 13.9, "bge-m3 embed\n(build time)",
        color=GREEN, fontsize=9, ha="center", va="center",
        fontweight="bold", zorder=7,
        bbox=dict(boxstyle="round,pad=0.25", facecolor=BG,
                  edgecolor=GREEN, linewidth=1, alpha=0.85))

# — Query-time: FastAPI ↔ RAG Pipeline ————————————————————————————————————
arr(8.95, 3.05, 9.30, 3.05, color=BLUE, lw=2.0, both=True)

# — Query-time: RAG → Supabase (vector search) ————————————————————————————
arr(13.80, 5.55, 13.80, 7.07, color=PURPLE, lw=1.8)
ax.text(14.35, 6.30, "vector\nsearch",
        color=PURPLE, fontsize=9, ha="left", va="center",
        fontweight="bold", zorder=7,
        bbox=dict(boxstyle="round,pad=0.22", facecolor=BG,
                  edgecolor=PURPLE, linewidth=1, alpha=0.85))

# — Query-time: RAG → llm-server (embed query) ————————————————————————————
arr(18.30, 3.40, 18.60, 13.25, color=BLUE, lw=1.8, rad=0.12)
ax.text(19.3, 8.3, "embed\nquery",
        color=BLUE, fontsize=9, ha="center", va="center",
        fontweight="bold", zorder=7,
        bbox=dict(boxstyle="round,pad=0.22", facecolor=BG,
                  edgecolor=BLUE, linewidth=1, alpha=0.85))

# — Query-time: RAG → Ollama Cloud (chat) —————————————————————————————————
arr(18.30, 4.20, 18.60, 16.00, color=ORANGE, lw=1.8, rad=0.08)
ax.text(19.6, 10.5, "LLM\nchat",
        color=ORANGE, fontsize=9, ha="center", va="center",
        fontweight="bold", zorder=7,
        bbox=dict(boxstyle="round,pad=0.22", facecolor=BG,
                  edgecolor=ORANGE, linewidth=1, alpha=0.85))

# — Browser ↔ FastAPI —————————————————————————————————————————————————————
arr(8.95, 5.22, 9.30, 5.22, color=PINK, lw=1.8, rad=0.0, both=True)
# label above connector
ax.text(9.12, 5.50, "HTTP/JSON", color=PINK, fontsize=8.5,
        ha="center", va="center", fontweight="bold", zorder=7)

# arrows between browser and RAG (just visual — through FastAPI)
arr(18.60, 3.05, 18.30, 3.05, color=PINK, lw=1.8)

# ═════════════════════════════════════════════════════════════════════════════
# 7.  LEGEND
# ═════════════════════════════════════════════════════════════════════════════
LX, LY, LW, LH = 18.65, 8.25, 8.8, 0.75
legend_items = [
    (PURPLE, "AI-assisted step (LLM)"),
    (GREEN,  "Embedding / Data write"),
    (BLUE,   "Vector search / API"),
    (ORANGE, "Cloud LLM (Ollama Cloud)"),
    (YELLOW, "Structured facts"),
    (PINK,   "Browser UI"),
]
rbox(LX, LY - len(legend_items)*LH - 0.2, LW, len(legend_items)*LH + 0.55,
     PANEL, SLATE, alpha=0.55, lw=1, radius=0.25)
txt(LX + LW/2, LY + 0.10, "Legend", MUTED, size=10, bold=True)
for k, (col, lbl) in enumerate(legend_items):
    cy = LY - 0.42 - k * LH
    dot = plt.Circle((LX + 0.38, cy), 0.15, color=col, alpha=0.85, zorder=7)
    ax.add_patch(dot)
    txt(LX + 0.68, cy, lbl, MUTED, size=9.5, ha="left")

# ═════════════════════════════════════════════════════════════════════════════
# 8.  SAVE
# ═════════════════════════════════════════════════════════════════════════════
OUT = r"D:\MyWorkSpace\RAG\enterprise-rag\architecture.jpg"
plt.tight_layout(pad=0)
plt.savefig(OUT, dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor(), format="jpeg",
            pil_kwargs={"quality": 95})
plt.close()
print(f"Saved  →  {OUT}")
