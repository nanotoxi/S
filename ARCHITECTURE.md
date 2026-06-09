# Sath Bot — Architecture & Design Document

## Overview

Sath Bot is a Telegram-based recruitment platform that works as a two-sided marketplace:

- **Employer side** — Conversational JD generation, then AI-powered resume matching
- **Candidate side** — Resume ingestion, gap analysis, profile enrichment, job preference capture

All interaction happens inside Telegram. The backend handles LLM calls (Groq), resume parsing, vector storage (RAG), and matching logic.

---

## User Flows

### Flow A: Employer / Company

```
User sends /start or /post_job
       │
       ▼
Bot identifies user as employer (or asks: "Are you hiring or looking for work?")
       │
       ▼
[JD Generation Wizard] — Groq LLM drives the conversation
  Questions asked (in sequence, skipping already-answered):
  1. Company name & industry
  2. Role title
  3. Employment type (full-time / part-time / contract / internship)
  4. Location (remote / hybrid / onsite + city)
  5. Years of experience required
  6. Key responsibilities (bullet points, user can send freely)
  7. Must-have skills
  8. Nice-to-have skills
  9. Educational qualifications
  10. Compensation range (optional)
  11. Any specific tools / tech stack
  12. Team size & reporting structure
  13. Any perks or unique selling points of the role
       │
       ▼
Bot drafts full JD using Groq API → sends preview to employer
       │
       ▼
Employer can: [Approve] / [Edit] / [Regenerate]
       │
       ▼
On approval → JD saved to DB + embedded into vector store
       │
       ▼
[Resume Matching] — RAG query against candidate vector store
  - Top-N matching resumes retrieved (configurable, default 10)
  - Each result shows: name, match score, key matching skills, years of exp
  - Employer can tap a result to see full resume summary
  - Option to "Request Contact" (notifies candidate via bot)
       │
       ▼
Employer dashboard (via /my_jobs): view all posted JDs, update, close
```

---

### Flow B: Candidate / Job Seeker

```
User sends /start or /upload_resume
       │
       ▼
Bot identifies user as candidate
       │
       ▼
[Resume Upload]
  - User sends PDF / DOCX / plain text
  - Bot parses resume → extracts structured data (see Resume Schema below)
       │
       ▼
[Gap Analysis] — compare extracted data against standard resume schema
  Bot asks about ONLY missing / weak fields, e.g.:
  - "I didn't find a summary/objective. Can you describe yourself in 2-3 sentences?"
  - "I see skills listed but no years of experience for each. How long have you used [X]?"
  - "No education section found. What's your highest qualification?"
  - "I noticed no certifications — do you have any relevant ones?"
  - "Your work experience entries are missing quantified achievements. Can you add impact numbers?"
       │
       ▼
[Job Preference Capture]
  1. What kind of role are you looking for?
  2. Preferred location / remote preference
  3. Expected salary / rate
  4. Available from (notice period / immediately)
  5. Open to contract / part-time / freelance?
       │
       ▼
[Social Profile Collection] (for cross-validation)
  - LinkedIn URL (primary — used to validate work history)
  - GitHub / Portfolio URL (for tech roles)
  - Instagram (optional — for design / creative roles)
  - Any other relevant link
  Bot notes: "These help employers verify your profile. Sharing is optional but recommended."
       │
       ▼
[Profile Complete] — resume embedded into vector store
  - Bot confirms profile is active and being matched
  - Candidate gets /my_profile to view, update, toggle visibility
       │
       ▼
[Job Match Notifications]
  - When a new JD is posted, bot proactively messages candidates whose
    vector similarity score exceeds threshold (configurable, default 0.78)
  - Message includes: role title, company (if public), key requirements, match score
  - Candidate can: [Interested] / [Not Interested] / [Snooze]
```

---

## Resume Schema (Standard Fields)

```json
{
  "personal": {
    "name": "",
    "email": "",
    "phone": "",
    "location": ""
  },
  "summary": "",
  "experience": [
    {
      "title": "",
      "company": "",
      "duration": "",
      "responsibilities": [],
      "achievements": []
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "year": "",
      "grade": ""
    }
  ],
  "skills": {
    "technical": [],
    "soft": []
  },
  "certifications": [],
  "projects": [
    {
      "name": "",
      "description": "",
      "tech_stack": [],
      "link": ""
    }
  ],
  "languages": [],
  "social": {
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "instagram": ""
  },
  "preferences": {
    "role_type": [],
    "location_preference": "",
    "salary_expectation": "",
    "available_from": "",
    "open_to_contract": false
  }
}
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        TELEGRAM                             │
│   Employer Chat          Candidate Chat                     │
└──────────┬──────────────────────┬───────────────────────────┘
           │  Webhook / Long Poll  │
           ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    BOT LAYER (Python)                       │
│  python-telegram-bot / aiogram                              │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │ Employer Router │    │     Candidate Router         │   │
│  │  /post_job      │    │  /upload_resume              │   │
│  │  /my_jobs       │    │  /my_profile                 │   │
│  │  /matches       │    │  /job_matches                │   │
│  └────────┬────────┘    └──────────┬───────────────────┘   │
└───────────┼──────────────────────┼──────────────────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICES                         │
│                                                             │
│  ┌────────────────┐   ┌───────────────┐  ┌──────────────┐  │
│  │  JD Generator  │   │Resume Parser  │  │  RAG Engine  │  │
│  │  (Groq API)    │   │(PyMuPDF +     │  │ (Embeddings  │  │
│  │                │   │ docx2txt +    │  │  + Vector DB)│  │
│  │  Wizard state  │   │ Groq extract) │  │              │  │
│  │  managed in    │   │               │  │  Similarity  │  │
│  │  Redis / DB    │   │               │  │  Search      │  │
│  └────────┬───────┘   └──────┬────────┘  └──────┬───────┘  │
│           │                  │                  │          │
│           └──────────────────┴──────────────────┘          │
│                              │                             │
│                    ┌─────────▼──────────┐                  │
│                    │   PostgreSQL DB     │                  │
│                    │  + pgvector ext.    │                  │
│                    │                    │                  │
│                    │  Tables:            │                  │
│                    │  - users            │                  │
│                    │  - employers        │                  │
│                    │  - candidates       │                  │
│                    │  - job_descriptions │                  │
│                    │  - resumes          │                  │
│                    │  - matches          │                  │
│                    │  - conversations    │                  │
│                    │  - notifications    │                  │
│                    └────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
            │                      │
            ▼                      ▼
┌────────────────────┐   ┌──────────────────────┐
│    Groq API        │   │  File Storage         │
│  (groq.com)        │   │  (Local / S3 / R2)   │
│  llama-3.3-70b /  │   │  - Raw resumes        │
│  mixtral-8x7b     │   │  - Processed JSONs    │
│  - JD drafting    │   └──────────────────────┘
│  - Resume parsing │
│  - Gap questions  │
│  - Match scoring  │
└────────────────────┘
```

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Bot framework | `python-telegram-bot` v21 (async) | Mature, well-documented, async support |
| LLM | Groq API (groq.com) — `llama-3.3-70b-versatile` | Ultra-fast inference, generous free tier |
| Resume parsing | PyMuPDF (PDF) + python-docx (DOCX) + Groq (extraction) | Multi-format; Groq handles messy layouts |
| Vector store | PostgreSQL + pgvector | Single DB, no extra infra; scales to millions of vectors |
| Embeddings | `sentence-transformers` `all-MiniLM-L6-v2` (local, free) | Groq has no embedding endpoint; local model keeps costs zero |
| Relational DB | PostgreSQL (Railway / local) | Battle-tested, pgvector support |
| State management | PostgreSQL (conversation_states table) | Persistent across restarts |
| File storage | Local filesystem → migrate to Cloudflare R2 | Start simple, upgrade later |
| Background jobs | Python asyncio + APScheduler | Proactive match notifications |
| Deployment | Railway (Docker) or VPS | Simple, cheap, always-on |
| Config | `.env` file | `python-dotenv` |

---

## Database Schema

```sql
-- Users (shared between both flows)
CREATE TABLE users (
    id BIGINT PRIMARY KEY,  -- Telegram user_id
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    user_type TEXT CHECK (user_type IN ('employer', 'candidate', 'both')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Employer profiles
CREATE TABLE employers (
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
CREATE TABLE job_descriptions (
    id SERIAL PRIMARY KEY,
    employer_id INT REFERENCES employers(id),
    title TEXT NOT NULL,
    full_jd TEXT NOT NULL,
    structured_jd JSONB,  -- parsed fields
    embedding VECTOR(1536),  -- pgvector
    status TEXT DEFAULT 'active' CHECK (status IN ('draft', 'active', 'closed')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Candidates
CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    resume_raw TEXT,
    resume_structured JSONB,  -- full schema
    embedding VECTOR(1536),
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
CREATE TABLE conversation_states (
    user_id BIGINT PRIMARY KEY REFERENCES users(id),
    flow TEXT,  -- 'jd_wizard' | 'resume_onboarding' | 'gap_fill'
    step TEXT,
    collected_data JSONB,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Match log
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    jd_id INT REFERENCES job_descriptions(id),
    candidate_id INT REFERENCES candidates(id),
    score FLOAT,
    employer_action TEXT,  -- 'viewed' | 'requested_contact' | 'ignored'
    candidate_action TEXT, -- 'interested' | 'not_interested' | 'snoozed'
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Notifications queue
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    type TEXT,
    payload JSONB,
    sent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## RAG / Matching Pipeline

```
JD Posted
    │
    ▼
Embed JD text → 1536-dim vector (stored in job_descriptions.embedding)
    │
    ▼
pgvector cosine similarity search against candidates.embedding
    │
    ▼
Top-N candidates sorted by score
    │
    ▼
Optional re-rank: Groq API prompt
  "Given this JD and this resume, score fit 0-100 and explain top 3 reasons"
    │
    ▼
Results sent to employer in Telegram

Candidate Uploads Resume
    │
    ▼
Parse → structured JSON → embed full profile text → store vector
    │
    ▼
Immediate: search active JDs for this candidate (reverse match)
    │
    ▼
Notify candidate of top matching open roles
```

---

## Project File Structure

```
sath_bot/
├── ARCHITECTURE.md          ← this file
├── .env                     ← secrets (never commit)
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
│
├── bot/
│   ├── __init__.py
│   ├── main.py              ← entry point, sets up Application
│   ├── config.py            ← loads env vars
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py         ← /start, user type detection
│   │   ├── employer.py      ← JD wizard, /post_job, /my_jobs, /matches
│   │   └── candidate.py     ← resume upload, gap fill, /my_profile
│   │
│   ├── conversations/
│   │   ├── __init__.py
│   │   ├── jd_wizard.py     ← ConversationHandler for JD creation
│   │   └── resume_wizard.py ← ConversationHandler for resume onboarding
│   │
│   └── keyboards.py         ← InlineKeyboardMarkup helpers
│
├── services/
│   ├── __init__.py
│   ├── llm.py               ← Groq API client (JD gen, parsing, Q generation)
│   ├── resume_parser.py     ← PDF/DOCX → raw text
│   ├── embedder.py          ← text → vector
│   ├── rag.py               ← pgvector search, re-ranking
│   └── notifier.py          ← async match notifications
│
├── db/
│   ├── __init__.py
│   ├── connection.py        ← asyncpg pool
│   ├── models.py            ← typed dataclasses / pydantic models
│   ├── migrations/
│   │   └── 001_init.sql
│   └── queries/
│       ├── users.py
│       ├── employers.py
│       ├── candidates.py
│       ├── jds.py
│       └── matches.py
│
└── utils/
    ├── __init__.py
    ├── text.py              ← chunking, cleaning helpers
    └── validation.py        ← URL validators, phone/email checks
```

---

## Environment Variables

```env
# Telegram
TELEGRAM_BOT_TOKEN=8806381929:AAFOdtpm5APU7FbhzwIeq6BhHdUejvD3df4

# Groq
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/sath_bot

# App
MAX_RESUME_MATCHES=10
MATCH_SCORE_THRESHOLD=0.78
MAX_FILE_SIZE_MB=10
```

---

## Key Design Decisions

1. **Single DB (PostgreSQL + pgvector)** — avoids running a separate vector DB (Pinecone, Qdrant). pgvector handles millions of vectors fine for this use case.

2. **Groq for all LLM calls** — JD drafting, resume extraction, gap question generation, and optional re-ranking all go through the same Groq client (`groq` Python SDK). One API key, one billing surface. Default model: `llama-3.3-70b-versatile`.

3. **Conversation state in DB (not Redis)** — simpler ops, persistent across restarts, queryable. Acceptable latency for a Telegram bot.

4. **python-telegram-bot ConversationHandler** — built-in state machine for multi-step wizards. Each question is a state transition.

5. **Proactive matching** — when a new JD is posted, the system immediately runs a reverse match and notifies qualifying candidates. This is the core value-add over static job boards.

6. **Social profiles are optional** — stored for employer cross-validation but never exposed publicly. Candidate controls visibility.

---

## Phase Plan

| Phase | Scope |
|---|---|
| **Phase 1** | Bot skeleton, /start flow, user type detection, DB setup |
| **Phase 2** | Candidate flow: resume upload, parsing, gap fill, profile storage |
| **Phase 3** | Employer flow: JD wizard, Groq JD generation, JD storage |
| **Phase 4** | RAG: embeddings, pgvector search, match results in Telegram |
| **Phase 5** | Proactive notifications, match feedback (interested / not) |
| **Phase 6** | Polish: /my_profile, /my_jobs, edit/delete, visibility toggle |
| **Phase 7** | Social profile validation, employer verification |
| **Phase 8** | Analytics, admin commands, rate limiting, spam protection |
