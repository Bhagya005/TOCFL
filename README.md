# AI-powered TOCFL A1 Study Dashboard

Local multi-user app for studying the first 300 TOCFL A1 vocabulary words from `CCCC_Vocabulary_2022.xlsx`, with flashcards, AI example sentences, tests, and progress tracking.

**Architecture:** Python FastAPI backend (learning logic, DB, tests, flashcards) + Next.js frontend (UI).

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

Open **http://localhost:3000**. Log in or create a user (up to 2 users). Use Dashboard, Flashcards, Tests, Leaderboard, Progress, Weak Words, and Word Bank.

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

## API (FastAPI)

- `POST /api/auth/login`, `POST /api/auth/register` – auth
- `GET /api/me` – current user (Bearer token)
- `GET /api/dashboard` – plan, summary, test results
- `GET /api/flashcards/today?day=1` – words for the day
- `POST /api/flashcards/answer` – submit flashcard (word_id, knew)
- `GET /api/tests/eligible?test_type=daily|weekly|final`
- `POST /api/tests/start` – get questions (body: test_type)
- `POST /api/tests/submit` – submit answers (body: test_type, answers)
- `GET /api/audio?text=...` – TTS audio (Bearer token)
- `GET /api/leaderboard`, `GET /api/progress`, `GET /api/weak-words`, `GET /api/word-bank`

## Data & caching

- SQLite DB: `cache/app.db`
- Audio: `cache/audio/`
- OpenAI results cached in SQLite (example sentences).

