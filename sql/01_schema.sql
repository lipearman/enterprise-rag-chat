create extension if not exists vector;

create table if not exists documents (
    id text primary key,
    url text,
    title text,
    heading text,
    heading_path jsonb,
    language text,
    category text,
    service text,
    topic text,
    page_type text,
    chunk_index int,
    chunk_size int,
    keywords jsonb,
    suggested_questions jsonb,
    content text,
    text_for_embedding text,
    embedding vector(1024),
    company_code text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists company_facts (
    id bigserial primary key,
    fact_type text,
    fact_value text,
    language text,
    source_url text,
    confidence float default 1,
    created_at timestamptz default now()
);

create table if not exists staff_contacts (
    id bigserial primary key,
    name text,
    position text,
    department text,
    email text,
    phone text,
    language text,
    source_url text,
    confidence float default 1,
    created_at timestamptz default now()
);

create table if not exists faq_items (
    id bigserial primary key,
    question text,
    answer text,
    category text,
    intent text,
    language text,
    source_url text,
    source_title text,
    source_heading text,
    confidence float default 0.8,
    embedding vector(1024),
    company_code text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists metadata_items (
    id bigserial primary key,
    document_id text,
    url text,
    title text,
    heading text,
    language text,
    category text,
    service text,
    topic text,
    page_type text,
    entities jsonb,
    keywords jsonb,
    intent_tags jsonb,
    created_at timestamptz default now()
);

create table if not exists knowledge_items (
    id bigserial primary key,
    source_id text,
    url text,
    title text,
    heading text,
    language text,
    category text,
    knowledge_type text,
    question text,
    answer text,
    facts jsonb,
    created_at timestamptz default now()
);

create table if not exists relationships (
    id bigserial primary key,
    subject text,
    predicate text,
    object text,
    subject_type text,
    object_type text,
    source_url text,
    confidence float default 0.8,
    created_at timestamptz default now()
);

alter table documents enable row level security;
alter table company_facts enable row level security;
alter table staff_contacts enable row level security;
alter table faq_items enable row level security;
alter table metadata_items enable row level security;
alter table knowledge_items enable row level security;
alter table relationships enable row level security;

create index if not exists documents_embedding_idx
on documents using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create index if not exists documents_company_code_idx
on documents (company_code);

create index if not exists faq_items_embedding_idx
on faq_items using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create index if not exists faq_items_company_code_idx
on faq_items (company_code);

create or replace function match_documents (
  query_embedding vector(1024),
  match_count int default 10,
  filter jsonb default '{}'
)
returns table (
  id text,
  company_code text,
  url text,
  title text,
  heading text,
  language text,
  category text,
  service text,
  topic text,
  page_type text,
  chunk_index int,
  content text,
  similarity float
)
language plpgsql
stable
as $$
begin
  return query
  select
    d.id, d.company_code, d.url, d.title, d.heading, d.language, d.category, d.service,
    d.topic, d.page_type, d.chunk_index, d.content,
    1 - (d.embedding <=> query_embedding) as similarity
  from documents d
  where
    d.embedding is not null
    and case when filter ? 'company_code' then d.company_code = filter->>'company_code' else true end
    and case when filter ? 'language' then d.language = filter->>'language' else true end
    and case when filter ? 'category' then d.category = filter->>'category' else true end
    and case when filter ? 'service' then d.service = filter->>'service' else true end
    and case when filter ? 'topic' then d.topic = filter->>'topic' else true end
    and case when filter ? 'page_type' then d.page_type = filter->>'page_type' else true end
  order by d.embedding <=> query_embedding
  limit match_count;
end;
$$;

create or replace function match_faq (
  query_embedding vector(1024),
  match_count int default 5,
  filter jsonb default '{}'
)
returns table (
  id bigint,
  company_code text,
  question text,
  answer text,
  category text,
  intent text,
  language text,
  source_url text,
  similarity float
)
language plpgsql
stable
as $$
begin
  return query
  select
    f.id, f.company_code, f.question, f.answer, f.category, f.intent, f.language, f.source_url,
    1 - (f.embedding <=> query_embedding) as similarity
  from faq_items f
  where
    f.embedding is not null
    and case when filter ? 'company_code' then f.company_code = filter->>'company_code' else true end
    and case when filter ? 'language' then f.language = filter->>'language' else true end
    and case when filter ? 'category' then f.category = filter->>'category' else true end
    and case when filter ? 'intent' then f.intent = filter->>'intent' else true end
  order by f.embedding <=> query_embedding
  limit match_count;
end;
$$;

notify pgrst, 'reload schema';
