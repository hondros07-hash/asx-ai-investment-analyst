-- V24.9: apply only after reviewing V24.6 schema and testing RLS with two accounts.
create table if not exists public.axia_research_journal (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 security_id text not null check (length(trim(security_id)) between 1 and 40),
 entry_type text not null check (entry_type in ('thesis','note','decision','review')),
 title text not null check (length(trim(title)) between 1 and 200),
 body text not null check (length(body) between 1 and 10000),
 evidence_refs jsonb not null default '[]'::jsonb check (jsonb_typeof(evidence_refs) = 'array'),
 recorded_at timestamptz not null default now(),
 archived_at timestamptz,
 revision_of uuid references public.axia_research_journal(id) on delete set null
);
create index if not exists axia_journal_owner_security_time on public.axia_research_journal(user_id,security_id,recorded_at desc);
alter table public.axia_research_journal enable row level security;
create policy axia_journal_owner on public.axia_research_journal for all to authenticated
 using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
-- Prevent linking a revision to a record owned by someone else, including direct DB writes.
create or replace function public.axia_journal_revision_guard() returns trigger
language plpgsql set search_path = '' as $$
begin
 if new.revision_of is not null and not exists (
  select 1 from public.axia_research_journal p
  where p.id = new.revision_of and p.user_id = new.user_id and p.security_id = new.security_id
 ) then raise exception 'Invalid journal revision reference'; end if;
 return new;
end $$;
create trigger axia_journal_revision_check before insert or update on public.axia_research_journal
 for each row execute function public.axia_journal_revision_guard();
-- App writes append new revisions. Production grants, trigger privileges and RLS must be reviewed.
