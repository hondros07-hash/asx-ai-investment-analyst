-- Chrímata V23.2.0 — Supabase Identity, Profiles & Entitlement Foundation
-- Run in the Supabase SQL editor/migration system.

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  home_market_override text,
  custom_market_slots text[] not null default '{}',
  updated_at timestamptz not null default now(),
  constraint profiles_market_slots_max5 check (cardinality(custom_market_slots) <= 5)
);

create table if not exists public.entitlements (
  user_id uuid primary key references auth.users(id) on delete cascade,
  plan text not null default 'free' check (plan in ('free','pro')),
  status text not null default 'active' check (status in ('active','trialing','past_due','canceled','expired')),
  valid_until timestamptz,
  provider_customer_ref text,
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.entitlements enable row level security;

revoke all on table public.profiles from anon, authenticated;
revoke all on table public.entitlements from anon, authenticated;
grant select, update on table public.profiles to authenticated;
grant select on table public.entitlements to authenticated;
grant all on table public.profiles to service_role;
grant all on table public.entitlements to service_role;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles for select to authenticated
using ((select auth.uid()) = id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own" on public.profiles for update to authenticated
using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

drop policy if exists "entitlements_select_own" on public.entitlements;
create policy "entitlements_select_own" on public.entitlements for select to authenticated
using ((select auth.uid()) = user_id);

-- No authenticated INSERT/UPDATE grant or policy exists for entitlements:
-- users cannot promote themselves to Pro.

create or replace function public.handle_chrimata_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles(id,email) values(new.id,new.email)
  on conflict(id) do nothing;
  insert into public.entitlements(user_id,plan,status) values(new.id,'free','active')
  on conflict(user_id) do nothing;
  return new;
end;
$$;

revoke all on function public.handle_chrimata_new_user() from public, anon, authenticated;

drop trigger if exists on_chrimata_auth_user_created on auth.users;
create trigger on_chrimata_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_chrimata_new_user();
