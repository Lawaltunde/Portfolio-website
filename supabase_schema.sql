-- Projects table
create table if not exists public.projects (
  id bigserial primary key,
  title text not null,
  description text not null,
  github_url text default ''::text,
  image_url text default ''::text,
  tech_stack text not null,
  created_at timestamptz default now(),
  created_by uuid default auth.uid()
);

-- Enable RLS
alter table public.projects enable row level security;

-- Admin governance via an explicit admins table (no service role in app, pure RLS by user id)
create table if not exists public.admins (
  user_id uuid primary key
);

-- Enable RLS on admins so the policy applies
alter table public.admins enable row level security;

-- Allow each authenticated user to read only their own row to check admin status
do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename  = 'admins'
      and policyname = 'admins_self_read'
  ) then
    create policy admins_self_read
      on public.admins
      for select
      to authenticated
      using (auth.uid() = user_id);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename  = 'projects'
      and policyname = 'projects_admin_all'
  ) then
    create policy projects_admin_all
      on public.projects
      for all
      using (exists (select 1 from public.admins a where a.user_id = auth.uid()))
      with check (exists (select 1 from public.admins a where a.user_id = auth.uid()));
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename  = 'projects'
      and policyname = 'projects_read_all'
  ) then
    create policy projects_read_all
      on public.projects for select using (true);
  end if;
end $$;

-- Allow authenticated users to insert their own projects.
create policy projects_owner_insert on public.projects
  for insert to authenticated
  with check (auth.uid() = created_by);

-- Allow authenticated users to update their own projects.
create policy projects_owner_update on public.projects
  for update to authenticated
  using (auth.uid() = created_by);

-- Allow authenticated users to delete their own projects.
create policy projects_owner_delete on public.projects
  for delete to authenticated
  using (auth.uid() = created_by);

-- Storage: buckets (idempotent)
do $$ begin
  perform storage.create_bucket('portfolio', public => true);
exception when others then null; end $$;

-- Storage policies (admin full, public read)
do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'storage'
      and tablename  = 'objects'
      and policyname = 'storage_admin_all'
  ) then
    create policy storage_admin_all on storage.objects for all
      using (exists (select 1 from public.admins a where a.user_id = auth.uid()))
      with check (exists (select 1 from public.admins a where a.user_id = auth.uid()));
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'storage'
      and tablename  = 'objects'
      and policyname = 'storage_public_read'
  ) then
    create policy storage_public_read on storage.objects for select
      using (bucket_id = 'portfolio');
  end if;
end $$;