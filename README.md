# Enterprise AI-Assisted Hybrid RAG

ระบบนี้ออกแบบสำหรับ Enterprise RAG บน Website + Supabase pgvector + Ollama + n8n

## 1) Setup

```bash
cd ~/enterprise-rag-ai
python3 -m venv ~/crawler-env
source ~/crawler-env/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

## 2) สร้าง table/function ใน Supabase

เปิด Supabase SQL Editor แล้วรัน:

```bash
cat sql/01_schema.sql
```

หรือ copy SQL จากไฟล์ `sql/01_schema.sql` ไปรัน

## 3) Run Pipeline ตามลำดับ

```bash
source ~/crawler-env/bin/activate

python scripts/01_crawl_website.py
python scripts/02_extract_sections.py
python scripts/03_clean_sections_ai.py
python scripts/04_semantic_chunking_ai.py
python scripts/05_embed_documents.py

python scripts/06_extract_facts.py
python scripts/07_import_facts.py

python scripts/08_generate_faq.py
python scripts/09_embed_faq.py

python scripts/10_extract_metadata.py
python scripts/11_extract_knowledge.py
python scripts/12_build_relationships.py

python scripts/16_eval_rag.py

python scripts/17_enterprise_chatbot.py
```

## 4) Runtime Retrieval

`17_enterprise_chatbot.py` ใช้ลำดับนี้:

```text
Question
↓
Intent Router
↓
AI Query Rewrite
↓
FAQ Retrieval
↓
Facts / Staff
↓
Hybrid Documents Search
↓
AI Reranker
↓
Grounding
↓
Final Answer
```

## 5) Output สำคัญ

```text
$CRAWL_DIR/raw_pages.jsonl
$CRAWL_DIR/all_sections.jsonl
$CRAWL_DIR/clean_sections.jsonl
$CRAWL_DIR/chunks.jsonl
$CRAWL_DIR/facts.jsonl
$CRAWL_DIR/staff.jsonl
$CRAWL_DIR/faq_items.jsonl
$CRAWL_DIR/metadata_items.jsonl
$CRAWL_DIR/knowledge_items.jsonl
$CRAWL_DIR/relationships.jsonl
$CRAWL_DIR/rag_eval_report.json
```
