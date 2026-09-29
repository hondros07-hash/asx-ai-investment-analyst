-- AXÍA research-memory foundation. Apply only after Supabase project review.
-- Uses authenticated user identity and RLS; no service-role credentials in browser.
create extension if not exists pgcrypto;

create table if not exists public.axia_research_snapshots (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  security_id text not null check (length(trim(security_id)) > 0),
  listing_currency text,
  observed_at timestamptz not null,
  recorded_at timestamptz not null default now(),
  metrics jsonb not null default '{}'::jsonb,
  provenance jsonb not null default '{}'::jsonb,
  schema_version integer not null default 1
);
create index if not exists axia_snapshots_owner_security_time
  on public.axia_research_snapshots (user_id, security_id, recorded_at desc);

create table if not exists public.axia_thesis_conditions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  security_id text not null check (length(trim(security_id)) > 0),
  label text not null check (length(trim(label)) > 0),
  metric text not null,
  operator text not null check (operator in ('>','>=','<','<=','==')),
  threshold numeric not null,
  period text not null,
  currency text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz
);
create index if not exists axia_conditions_owner_security
  on public.axia_thesis_conditions (user_id, security_id);

create table if not exists public.axia_thesis_observations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  condition_id uuid not null,
  state text not null check (state in ('supported','contradicted','unverified','not_applicable')),
  evidence_digest text,
  evidence jsonb,
  observed_at timestamptz not null,
  recorded_at timestamptz not null default now(),
  foreign key (condition_id) references public.axia_thesis_conditions(id) on delete cascade
);
create index if not exists axia_observations_owner_condition_time
  on public.axia_thesis_observations (user_id, condition_id, recorded_at desc);

alter table public.axia_research_snapshots enable row level security;
alter table public.axia_thesis_conditions enable row level security;
alter table public.axia_thesis_observations enable row level security;

create policy axia_snapshots_own on public.axia_research_snapshots
  for all to authenticated using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));
create policy axia_conditions_own on public.axia_thesis_conditions
  for all to authenticated using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));
create policy axia_observations_own on public.axia_thesis_observations
  for all to authenticated using (
    user_id = (select auth.uid()) and exists (
      select 1 from public.axia_thesis_conditions c
      where c.id = condition_id and c.user_id = (select auth.uid())
    )
  )
  with check (
    user_id = (select auth.uid()) and exists (
      select 1 from public.axia_thesis_conditions c
      where c.id = condition_id and c.user_id = (select auth.uid())
    )
  );
-- No grant to anon. Audit production permissions and migrations before applying.
