-- V23.4.5: eligibility is controlled by trusted backend; auth confirmation alone
-- never grants Premium access. Apply this migration before deploying the new API.
create table if not exists public.trial_registration_attempts (
 id bigint generated always as identity primary key,
 email_key text not null, device_key text,
 status text not null default 'pending' check(status in ('pending','completed','failed')),
 created_at timestamptz not null default now(),
 check(email_key ~ '^[a-f0-9]{64}$'),
 check(device_key is null or device_key ~ '^[a-f0-9]{64}$')
);
create index if not exists trial_attempt_email_idx on public.trial_registration_attempts(email_key,created_at desc);
create index if not exists trial_attempt_device_idx on public.trial_registration_attempts(device_key,created_at desc) where device_key is not null;
alter table public.trial_registration_attempts enable row level security;
revoke all on public.trial_registration_attempts from anon,authenticated;

create table if not exists public.trial_eligibility (
 user_id uuid primary key references auth.users(id) on delete cascade,
 email_key text not null, device_key text,
 decision text not null check(decision in ('eligible','ineligible','review')),
 reason_code text not null,
 decided_at timestamptz not null default now(),
 unique(email_key)
);
create index if not exists trial_eligibility_device_idx on public.trial_eligibility(device_key) where device_key is not null;
alter table public.trial_eligibility enable row level security;
revoke all on public.trial_eligibility from anon,authenticated;

-- Replace old auth triggers: verification does not automatically grant a trial.
create or replace function public.handle_chrimata_email_verified()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
 if old.email_confirmed_at is null and new.email_confirmed_at is not null then
  update public.entitlements set status='active',updated_at=now() where user_id=new.id and status='pending_verification';
 end if;
 return new;
end; $$;
create or replace function public.handle_chrimata_new_user()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
 insert into public.profiles(id,email) values(new.id,new.email)
 on conflict(id) do update set email=excluded.email,updated_at=now();
 insert into public.entitlements(user_id,plan,status,trial_started_at,trial_ends_at)
 values(new.id,'free',case when new.email_confirmed_at is null then 'pending_verification' else 'active' end,null,null)
 on conflict(user_id) do nothing;
 return new;
end; $$;
revoke all on function public.handle_chrimata_email_verified() from public,anon,authenticated;
revoke all on function public.handle_chrimata_new_user() from public,anon,authenticated;

-- One atomic server-only grant; row lock prevents simultaneous eligibility races.
create or replace function public.finalize_chrimata_trial(p_user_id uuid,p_email_key text,p_device_key text default null)
returns text language plpgsql security definer set search_path = '' as $$
declare v_decision text; v_confirmed timestamptz; v_email text; v_prior boolean; v_device_seen boolean;
begin
 if auth.role() <> 'service_role' then raise exception 'Forbidden'; end if;
 select email,email_confirmed_at into v_email,v_confirmed from auth.users where id=p_user_id for update;
 if not found or v_confirmed is null then raise exception 'Verified account required'; end if;
 if p_email_key !~ '^[a-f0-9]{64}$' or (p_device_key is not null and p_device_key !~ '^[a-f0-9]{64}$') then raise exception 'Invalid signal'; end if;
 -- A pre-signup server-recorded signal must exist; a client cannot invent a claim.
 if not exists(select 1 from public.trial_registration_attempts where email_key=p_email_key and status='pending') then
  raise exception 'Registration signal missing';
 end if;
 select decision into v_decision from public.trial_eligibility where user_id=p_user_id;
 if v_decision is not null then return v_decision; end if;
 perform pg_advisory_xact_lock(hashtextextended(p_email_key,0));
 select exists(select 1 from public.trial_eligibility where email_key=p_email_key) into v_prior;
 select exists(select 1 from public.trial_eligibility where device_key=p_device_key and p_device_key is not null) into v_device_seen;
 v_decision:=case when v_prior then 'ineligible' when v_device_seen then 'review' else 'eligible' end;
 insert into public.trial_eligibility(user_id,email_key,device_key,decision,reason_code)
 values(p_user_id,p_email_key,p_device_key,v_decision,case when v_prior then 'prior_identity' when v_device_seen then 'shared_device_review' else 'new_verified_account' end);
 if v_decision='eligible' then
  update public.entitlements set trial_started_at=now(),trial_ends_at=now()+interval '30 days',status='active',updated_at=now()
  where user_id=p_user_id and trial_started_at is null and trial_ends_at is null;
 end if;
 update public.trial_registration_attempts set status='completed' where email_key=p_email_key and status='pending';
 return v_decision;
end; $$;
revoke all on function public.finalize_chrimata_trial(uuid,text,text) from public,anon,authenticated;
grant execute on function public.finalize_chrimata_trial(uuid,text,text) to service_role;
