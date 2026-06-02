# Enterprise RAG Chat UI

## Run

```bash
cd ~/enterprise-rag-ai
uvicorn app:app --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080
```

## Features

- แสดง Provider ปัจจุบัน: local/cloud, base_url, model
- Chat UI ภาษาไทย
- URL ในคำตอบกดได้อัตโนมัติ
- เก็บประวัติใน browser localStorage
- Copy คำตอบล่าสุด
- Stop request
- Prompt ตัวอย่าง

## API used by UI

- `GET /provider`
- `POST /chat`
- `GET /health`
