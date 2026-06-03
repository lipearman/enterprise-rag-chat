"""
migrate_to_supabase_cloud.py
────────────────────────────
ย้ายข้อมูลทุกตารางจาก Supabase เก่า (self-hosted) ไปยัง Supabase Cloud

OLD  : http://llm-server:8000   (SUPABASE_OLD_URL / SUPABASE_OLD_KEY)
NEW  : https://joqnuzjwawpejxtakzcc.supabase.co  (SUPABASE_URL / SUPABASE_KEY)

Usage:
    python scripts/migrate_to_supabase_cloud.py
    python scripts/migrate_to_supabase_cloud.py --tables documents faq_items
    python scripts/migrate_to_supabase_cloud.py --batch-size 50
"""

import argparse
import os
import sys
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
OLD_URL = os.getenv("SUPABASE_OLD_URL", "http://llm-server:8000")
OLD_KEY = os.getenv("SUPABASE_OLD_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3Nzc1Njg0MDAsImV4cCI6MTkzNTMzNDgwMH0."
    "6m92O1-T55zE62I2Zf2GvNLL4-D8T1byzla58-bnRjI")

NEW_URL = os.getenv("SUPABASE_URL")
NEW_KEY = os.getenv("SUPABASE_KEY")

OLD_HDR = {
    "apikey": OLD_KEY,
    "Authorization": f"Bearer {OLD_KEY}",
    "Content-Type": "application/json",
}
NEW_HDR = {
    "apikey": NEW_KEY,
    "Authorization": f"Bearer {NEW_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# ── Table definitions ────────────────────────────────────────────────────────
# vector_cols: columns ที่เป็น vector type — PostgREST ส่งมาเป็น string "[...]"
# pk: primary key column สำหรับ upsert
TABLES = [
    {"name": "company_facts",   "pk": "id",  "vector_cols": []},
    {"name": "staff_contacts",  "pk": "id",  "vector_cols": []},
    {"name": "relationships",   "pk": "id",  "vector_cols": []},
    {"name": "metadata_items",  "pk": "id",  "vector_cols": []},
    {"name": "knowledge_items", "pk": "id",  "vector_cols": []},
    {"name": "faq_items",       "pk": "id",  "vector_cols": ["embedding"]},
    {"name": "documents",       "pk": "id",  "vector_cols": ["embedding"]},
]

BATCH_SIZE = 100   # rows per request (ลดถ้า payload ใหญ่เกิน)
RETRY_MAX  = 3
RETRY_WAIT = 5     # seconds


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_count(url: str, hdr: dict, table: str) -> int:
    r = requests.get(
        f"{url}/rest/v1/{table}?select=count",
        headers={**hdr, "Prefer": "count=exact"},
        timeout=30,
    )
    cr = r.headers.get("content-range", "0/0")
    return int(cr.split("/")[-1]) if "/" in cr else 0


def fetch_batch(url: str, hdr: dict, table: str, offset: int, limit: int) -> list[dict]:
    r = requests.get(
        f"{url}/rest/v1/{table}?select=*&offset={offset}&limit={limit}",
        headers=hdr,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def fix_vectors(rows: list[dict], vector_cols: list[str]) -> list[dict]:
    """PostgREST returns vectors as string '[0.1,0.2,...]' — keep as-is,
    Supabase Cloud accepts that format for INSERT."""
    return rows


def upsert_batch(url: str, hdr: dict, table: str, rows: list[dict], pk: str) -> None:
    for attempt in range(1, RETRY_MAX + 1):
        r = requests.post(
            f"{url}/rest/v1/{table}",
            headers={**hdr, "Prefer": f"resolution=merge-duplicates,return=minimal"},
            json=rows,
            timeout=120,
        )
        if r.status_code in (200, 201, 204):
            return
        if attempt < RETRY_MAX:
            print(f"      [retry {attempt}] status={r.status_code} — {r.text[:120]}")
            time.sleep(RETRY_WAIT)
        else:
            raise RuntimeError(
                f"upsert failed after {RETRY_MAX} attempts: "
                f"status={r.status_code}  body={r.text[:300]}"
            )


def migrate_table(table_def: dict, batch_size: int) -> None:
    name       = table_def["name"]
    pk         = table_def["pk"]
    vector_cols = table_def["vector_cols"]

    total = get_count(OLD_URL, OLD_HDR, name)
    print(f"\n{'─'*60}")
    print(f"  {name}  ({total:,} rows)")
    print(f"{'─'*60}")

    if total == 0:
        print("  ไม่มีข้อมูล — ข้ามตารางนี้")
        return

    migrated = 0
    offset   = 0
    errors   = 0

    while offset < total:
        rows = fetch_batch(OLD_URL, OLD_HDR, name, offset, batch_size)
        if not rows:
            break

        rows = fix_vectors(rows, vector_cols)

        try:
            upsert_batch(NEW_URL, NEW_HDR, name, rows, pk)
            migrated += len(rows)
        except RuntimeError as e:
            errors += len(rows)
            print(f"  ❌ ERROR offset={offset}: {e}")

        offset += len(rows)
        pct = migrated / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  [{bar}] {migrated:,}/{total:,} ({pct:.1f}%)", end="\r", flush=True)

    print(f"  [{('█'*20)}] {migrated:,}/{total:,} (100.0%)  errors={errors}")
    return migrated, errors


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Migrate Supabase data to cloud")
    parser.add_argument("--tables", nargs="+", help="ระบุชื่อตารางที่ต้องการ migrate (default: ทั้งหมด)")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help=f"rows per batch (default: {BATCH_SIZE})")
    args = parser.parse_args()

    if not NEW_URL or not NEW_KEY:
        print("ERROR: SUPABASE_URL / SUPABASE_KEY ไม่ได้ตั้งค่าใน .env")
        sys.exit(1)

    print("=" * 60)
    print("  Supabase Data Migration")
    print("=" * 60)
    print(f"  OLD: {OLD_URL}")
    print(f"  NEW: {NEW_URL}")
    print(f"  Batch size: {args.batch_size}")

    # filter tables if requested
    tables = TABLES
    if args.tables:
        tables = [t for t in TABLES if t["name"] in args.tables]
        if not tables:
            print(f"ERROR: ไม่พบตาราง {args.tables}")
            sys.exit(1)

    # verify old connection
    print("\n  ตรวจสอบ connection...")
    try:
        r = requests.get(f"{OLD_URL}/rest/v1/", headers=OLD_HDR, timeout=10)
        print(f"  OLD Supabase: {'OK' if r.ok else 'ERROR ' + str(r.status_code)}")
    except Exception as e:
        print(f"  OLD Supabase: ERROR — {e}")
        sys.exit(1)

    try:
        r = requests.get(f"{NEW_URL}/rest/v1/", headers=NEW_HDR, timeout=10)
        print(f"  NEW Supabase: {'OK' if r.ok else 'ERROR ' + str(r.status_code)}")
    except Exception as e:
        print(f"  NEW Supabase: ERROR — {e}")
        sys.exit(1)

    # migrate
    start_time = time.time()
    total_migrated = 0
    total_errors   = 0

    for tdef in tables:
        result = migrate_table(tdef, args.batch_size)
        if result:
            m, e = result
            total_migrated += m
            total_errors   += e

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  เสร็จสิ้น!")
    print(f"  ย้ายสำเร็จ : {total_migrated:,} rows")
    print(f"  Error      : {total_errors:,} rows")
    print(f"  เวลาที่ใช้  : {elapsed:.1f} วินาที")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
