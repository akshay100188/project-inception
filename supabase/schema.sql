-- Run this in your Supabase SQL editor.
--
-- Only needed for DEMO_MODE=true, which grounds the Claude agents with a
-- pgvector corpus. The default (rule-based, ephemeral) app needs no database —
-- it stores nothing and has no accounts.
--
-- ────────────────────────────────────────────────────────────
-- pgvector RAG corpus (DEMO_MODE only)
-- ────────────────────────────────────────────────────────────

create extension if not exists vector;

create table if not exists public.rag_corpus (
  id          uuid primary key default gen_random_uuid(),
  category    text not null check (category in ('architecture', 'techstack', 'estimation', 'project_example')),
  title       text not null,
  content     text not null,
  embedding   vector(1536),
  metadata    jsonb default '{}'::jsonb,
  created_at  timestamptz not null default now()
);

create index if not exists rag_corpus_embedding_idx
  on public.rag_corpus using ivfflat (embedding vector_cosine_ops)
  with (lists = 10);

-- ────────────────────────────────────────────────────────────
-- Migration M001: add project_example category
-- Run ONCE in Supabase SQL editor if rag_corpus already exists
-- (skip if running schema.sql fresh — the constraint below already includes it)
-- ────────────────────────────────────────────────────────────
-- ALTER TABLE public.rag_corpus DROP CONSTRAINT rag_corpus_category_check;
-- ALTER TABLE public.rag_corpus ADD CONSTRAINT rag_corpus_category_check
--   CHECK (category IN ('architecture', 'techstack', 'estimation', 'project_example'));
--
-- Then run: python -m scripts.migrate_examples_to_supabase

create or replace function public.match_corpus(
  query_embedding vector(1536),
  match_category  text,
  match_count     int default 4
)
returns table (id uuid, title text, content text, similarity float)
language sql stable
as $$
  select id, title, content,
         1 - (embedding <=> query_embedding) as similarity
  from public.rag_corpus
  where category = match_category
    and embedding is not null
  order by embedding <=> query_embedding
  limit match_count;
$$;
