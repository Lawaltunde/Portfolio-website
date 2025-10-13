-- Projects table
create table if not exists public.projects (
  id bigserial primary key,
  title text not null,
  description text not null,
  github_url text,
  image_url text,
  tech_stack text,
  created_at timestamptz default now(),
  created_by uuid default auth.uid()
);

-- Blogs table
create table if not exists public.blog_posts (
  id bigserial primary key,
  title text not null,
  content text not null,
  created_at timestamptz default now(),
  created_by uuid default auth.uid()
);

-- Enable RLS
alter table public.projects enable row level security;
alter table public.blog_posts enable row level security;

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
      and tablename  = 'blog_posts'
      and policyname = 'blog_admin_all'
  ) then
    create policy blog_admin_all
      on public.blog_posts
      for all
      using (exists (select 1 from public.admins a where a.user_id = auth.uid()))
      with check (exists (select 1 from public.admins a where a.user_id = auth.uid()));
  end if;
end $$;

-- Public read policy
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

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename  = 'blog_posts'
      and policyname = 'blog_read_all'
  ) then
    create policy blog_read_all
      on public.blog_posts for select using (true);
  end if;
end $$;

-- Optional: owner-based writes for non-admins (keep disabled by default)
-- create policy projects_owner_write on public.projects for insert to authenticated using (true) with check (auth.uid() = created_by);
-- create policy blog_owner_write on public.blog_posts for insert to authenticated using (true) with check (auth.uid() = created_by);

-- Storage: buckets (idempotent)
do $$ begin
  perform storage.create_bucket('portfolio', public => true);
exception when others then null; end $$;
do $$ begin
  perform storage.create_bucket('blogs', public => true);
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
      using (bucket_id in ('portfolio','blogs'));
  end if;
end $$;
