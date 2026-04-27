create extension if not exists "pgcrypto";

create table if not exists analyses (
  id uuid primary key default gen_random_uuid(),
  topic text not null,
  location text,
  category text,
  status text not null default 'pending' check (status in ('pending', 'crawling', 'scraping', 'analyzing', 'completed', 'failed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references analyses(id) on delete cascade,
  url text not null,
  title text,
  source_type text not null default 'web',
  status text not null default 'pending' check (status in ('pending', 'scraping', 'completed', 'failed', 'skipped')),
  created_at timestamptz not null default now()
);

create table if not exists scraped_items (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references analyses(id) on delete cascade,
  source_id uuid references sources(id) on delete set null,
  name text,
  description text,
  address text,
  price_text text,
  price_min numeric,
  price_max numeric,
  rating numeric,
  review_count integer,
  raw_text text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists insights (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null unique references analyses(id) on delete cascade,
  summary text,
  opportunities jsonb not null default '[]'::jsonb,
  competitors jsonb not null default '[]'::jsonb,
  pricing_insight text,
  customer_pain_points jsonb not null default '[]'::jsonb,
  strategy_recommendations jsonb not null default '[]'::jsonb,
  raw_ai_response jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists discovery_profiles (
  id uuid primary key default gen_random_uuid(),
  profile_key text not null unique,
  label text,
  topic_hints jsonb not null default '[]'::jsonb,
  query_boosters jsonb not null default '[]'::jsonb,
  required_terms jsonb not null default '[]'::jsonb,
  preferred_domains jsonb not null default '[]'::jsonb,
  blocked_terms jsonb not null default '[]'::jsonb,
  source_type_map jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_analyses_status_created_at on analyses(status, created_at desc);
create index if not exists idx_sources_analysis_id on sources(analysis_id);
create index if not exists idx_scraped_items_analysis_id on scraped_items(analysis_id);
create index if not exists idx_insights_analysis_id on insights(analysis_id);
create index if not exists idx_discovery_profiles_active on discovery_profiles(is_active);

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_analyses_updated_at on analyses;
create trigger trg_analyses_updated_at
before update on analyses
for each row
execute function set_updated_at();

drop trigger if exists trg_discovery_profiles_updated_at on discovery_profiles;
create trigger trg_discovery_profiles_updated_at
before update on discovery_profiles
for each row
execute function set_updated_at();
