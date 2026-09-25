-- Chrímata V23.3.0 — Registration, 30-Day Trial & 3-Tier Entitlements

alter table public.entitlements drop constraint if exists entitlements_plan_check;
alter table public.entitlements drop constraint if exists entitlements_status_check;

alter table public.entitlements
  add column if not exists trial_started_at timestamptz,
  add column if not exists trial_ends_at timestamptz,
  add column if not exists billing_interval text;

alter table public.entitlements
  add constraint entitlements_plan_check check (plan in ('free','general','premium')),
  add constraint entitlements_status_check check (status in ('pending_verification','active','trialing','past_due','canceled','expired')),
  add constraint entitlements_billing_interval_check check (billing_interval is null or billing_interval in ('monthly','yearly')),
  add constraint entitlements_trial_window_check check (trial_ends_at is null or trial_started_at is null or trial_ends_at > trial_started_at);

-- Replace V23.2.0 signup trigger: create a Free entitlement, but do NOT start the
-- 30-day trial until Supabase records email confirmation.
create or replace function public.handle_chrimata_new_user()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  insert into public.profiles(id,email) values(new.id,new.email)
  on conflict(id) do update set email=excluded.email, updated_at=now();
  insert into public.entitlements(user_id,plan,status)
  values(new.id,'free',case when new.email_confirmed_at is null then 'pending_verification' else 'active' end)
  on conflict(user_id) do nothing;
  return new;
end;
$$;

create or replace function public.handle_chrimata_email_verified()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  if old.email_confirmed_at is null and new.email_confirmed_at is not null then
    update public.entitlements
       set status='active',
           trial_started_at=coalesce(trial_started_at,now()),
           trial_ends_at=coalesce(trial_ends_at,now()+interval '30 days'),
           updated_at=now()
     where user_id=new.id;
  end if;
  return new;
end;
$$;

revoke all on function public.handle_chrimata_new_user() from public,anon,authenticated;
revoke all on function public.handle_chrimata_email_verified() from public,anon,authenticated;

drop trigger if exists on_chrimata_auth_user_verified on auth.users;
create trigger on_chrimata_auth_user_verified
after update of email_confirmed_at on auth.users
for each row execute procedure public.handle_chrimata_email_verified();

-- Backstop: if email confirmation is disabled and a user arrives already confirmed,
-- initialize the trial on insert without making entitlement fields client-editable.
create or replace function public.handle_chrimata_new_user()
returns trigger language plpgsql security definer set search_path = ''
as $$
declare is_confirmed boolean := new.email_confirmed_at is not null;
begin
  insert into public.profiles(id,email) values(new.id,new.email)
  on conflict(id) do update set email=excluded.email, updated_at=now();
  insert into public.entitlements(user_id,plan,status,trial_started_at,trial_ends_at)
  values(new.id,'free',case when is_confirmed then 'active' else 'pending_verification' end,
         case when is_confirmed then now() else null end,
         case when is_confirmed then now()+interval '30 days' else null end)
  on conflict(user_id) do nothing;
  return new;
end;
$$;
revoke all on function public.handle_chrimata_new_user() from public,anon,authenticated;
