-- Run this in your Supabase SQL editor

create table if not exists public.incept_projects (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  raw_input   text not null,
  status      text not null default 'drafting'
              check (status in ('drafting','clarifying','planning','reviewing','complete')),
  requirements    jsonb,
  clarifications  jsonb,
  plan            jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Row-level security: users can only see their own projects
alter table public.incept_projects enable row level security;

create policy "incept: users can manage own projects"
  on public.incept_projects
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Auto-update updated_at
create or replace function public.handle_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger incept_projects_updated_at
  before update on public.incept_projects
  for each row execute procedure public.handle_updated_at();

-- ────────────────────────────────────────────────────────────
-- Phase 2: pgvector RAG corpus
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
