-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users (shared between both flows)
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,  -- Telegram user_id
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    user_type TEXT CHECK (user_type IN ('employer', 'candidate', 'both')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Employer profiles
CREATE TABLE IF NOT EXISTS employers (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    company_name TEXT,
    industry TEXT,
    company_size TEXT,
    website TEXT,
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Job Descriptions
CREATE TABLE IF NOT EXISTS job_descriptions (
    id SERIAL PRIMARY KEY,
    employer_id INT REFERENCES employers(id),
    title TEXT NOT NULL,
    full_jd TEXT NOT NULL,
    structured_jd JSONB,  -- parsed fields
    embedding VECTOR(384),  -- MiniLM-L6-v2 is 384 dimensions
    status TEXT DEFAULT 'active' CHECK (status IN ('draft', 'active', 'closed')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Candidates
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE REFERENCES users(id),
    resume_raw TEXT,
    resume_structured JSONB,  -- full schema
    embedding VECTOR(384),
    profile_complete BOOLEAN DEFAULT false,
    visible BOOLEAN DEFAULT true,
    social_linkedin TEXT,
    social_github TEXT,
    social_instagram TEXT,
    social_portfolio TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Conversation state (wizard progress)
CREATE TABLE IF NOT EXISTS conversation_states (
    user_id BIGINT PRIMARY KEY REFERENCES users(id),
    flow TEXT,  -- 'jd_wizard' | 'resume_onboarding' | 'gap_fill'
    step TEXT,
    collected_data JSONB,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Match log
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    jd_id INT REFERENCES job_descriptions(id),
    candidate_id INT REFERENCES candidates(id),
    score FLOAT,
    employer_action TEXT,  -- 'viewed' | 'requested_contact' | 'ignored'
    candidate_action TEXT, -- 'interested' | 'not_interested' | 'snoozed'
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Notifications queue
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    type TEXT,
    payload JSONB,
    sent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Ensure unique constraint on candidates.user_id (handles DBs created before UNIQUE was in schema)
CREATE UNIQUE INDEX IF NOT EXISTS candidates_user_id_unique ON candidates(user_id);
