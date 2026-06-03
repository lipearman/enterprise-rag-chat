-- ============================================================
--  02_alter_add_missing_columns.sql
--  เพิ่ม columns ที่ขาดหายไปใน schema เดิม (01_schema.sql)
--  รันใน Supabase SQL Editor ก่อนทำ migration
-- ============================================================

-- company_facts
alter table company_facts
    add column if not exists company_code text,
    add column if not exists updated_at   timestamptz default now();

-- staff_contacts
alter table staff_contacts
    add column if not exists company_code text,
    add column if not exists updated_at   timestamptz default now();

-- metadata_items
alter table metadata_items
    add column if not exists company_code text,
    add column if not exists updated_at   timestamptz default now();

-- knowledge_items
alter table knowledge_items
    add column if not exists company_code text,
    add column if not exists updated_at   timestamptz default now();

-- relationships
alter table relationships
    add column if not exists source_type  text,
    add column if not exists company_code text,
    add column if not exists updated_at   timestamptz default now();

-- reload PostgREST schema cache
notify pgrst, 'reload schema';
