# AI-powered TOCFL A1 Study Dashboard

Local multi-user app for studying the first 300 TOCFL A1 vocabulary words from `CCCC_Vocabulary_2022.xlsx`, with flashcards, AI example sentences, tests, and progress tracking.

**Architecture (Vercel deploy):** Next.js frontend + API routes (serverless) + Supabase (PostgreSQL). No separate backend; all APIs live under `/api` and use Supabase for persistence.

**Legacy (local):** Python FastAPI backend + SQLite + Next.js frontend (see Setup below).

## Setup

### 1) Create a virtual environment (recommended)

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 2) Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment variables

- Copy `.env.example` to `.env`
- Set:
  - `OPENAI_API_KEY` (optional but recommended)
  - `OPENAI_MODEL` (optional, default: `gpt-4o-mini`)
  - `JWT_SECRET` (optional, for production; default is a dev secret)

### 4) Put the Excel file in the project root

- `CCCC_Vocabulary_2022.xlsx`

### 5) Run the backend API

From the project root:

```bash
python app.py
```

This starts the FastAPI server at **http://localhost:8000**.

### 6) Run the Next.js frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. Log in or create a user (up to 5 users). Use Dashboard, Flashcards, Tests, Leaderboard, Progress, Weak Words, and Word Bank.

## Deploy full stack on Vercel (Supabase)

1. **Supabase:** Create a project at [supabase.com](https://supabase.com). In the SQL Editor, run the migration in `frontend/supabase/migrations/001_initial.sql`.
2. **Seed words:** From the project root, with `CCCC_Vocabulary_2022.xlsx` in place and Supabase env vars set (e.g. from `frontend/.env.local` or exported), run:
   ```bash
   python scripts/seed_supabase_words.py
   ```
   This fills the `words` table (and optionally `examples`) with the first 300 TOCFL words. Without this, the flashcard and word-bank pages will be empty.
3. **Vercel:** Set **Root Directory** to `frontend`. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL` – Supabase project URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` or `SUPABASE_SERVICE_ROLE_KEY` – API key (service role recommended for API routes)
   - `JWT_SECRET` – secret for auth tokens
4. Deploy. The app uses same-origin `/api` routes; no separate backend URL.

**Build without Supabase:** For a local build (e.g. CI) without real credentials, set placeholders: `NEXT_PUBLIC_SUPABASE_URL=https://placeholder.supabase.co` and `SUPABASE_ANON_KEY=placeholder`.

**Audio:** `/api/audio` returns 501 unless you set `TTS_API_URL` to a TTS service. The UI can fall back to browser speech synthesis.

## Routes (Next.js)

| Path | Description |
|------|-------------|
| `/` | Redirects to dashboard or login |
| `/login` | Log in / Create user |
| `/dashboard` | Overview and test scores |
| `/flashcards` | Today's flashcards |
| `/tests` | Daily / Weekly / Final test selection |
| `/tests/daily`, `/tests/weekly`, `/tests/final` | Run a test |
| `/leaderboard` | Leaderboard |
| `/progress` | Progress and accuracy by word |
| `/weak-words` | Weak words |
| `/word-bank` | Full word bank with filters |

## API (Next.js + Supabase)

- `POST /api/auth/login`, `POST /api/auth/register` – auth
- `GET /api/me` – current user (Bearer token)
- `GET /api/dashboard` – plan, summary, test results
- `GET /api/flashcards/today?day=1` – words for the day
- `POST /api/flashcards/answer` – submit flashcard (word_id, knew)
- `GET /api/tests/eligible?test_type=daily|weekly|final`
- `POST /api/tests/start` – get questions (body: test_type)
- `POST /api/tests/submit` – submit answers (body: test_type, answers)
- `GET /api/audio?text=...` – TTS audio (optional; set TTS_API_URL or use client fallback)
- `GET /api/leaderboard`, `GET /api/progress`, `GET /api/weak-words`, `GET /api/word-bank`

## Data & caching

- **Vercel + Supabase:** All data in Supabase (users, words, user_progress, test_results, etc.). See `frontend/supabase/migrations/001_initial.sql`.
- **Local (legacy):** SQLite `cache/app.db`, audio in `cache/audio/`.

