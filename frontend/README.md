# TOCFL A1 Frontend (Next.js)

This is the Next.js frontend for the TOCFL A1 Study app. The Python backend runs separately and exposes a REST API.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create `.env.local` (optional):
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
   If omitted, the app uses `http://localhost:8000` by default.

3. Start the Python API from the **project root**:
   ```bash
   python app.py
   ```
   Or: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`

4. Start the Next.js dev server:
   ```bash
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000). Log in or create a user, then use Dashboard, Flashcards, Tests, Leaderboard, Progress, Weak Words, and Word Bank.

## Routes

| Path | Description |
|------|-------------|
| `/` | Redirects to `/dashboard` or `/login` |
| `/login` | Log in / Create user |
| `/dashboard` | Overview and test scores |
| `/flashcards` | Today's flashcards |
| `/tests` | Test type selection (Daily / Weekly / Final) |
| `/tests/daily`, `/tests/weekly`, `/tests/final` | Run a test |
| `/leaderboard` | Leaderboard |
| `/progress` | Progress and accuracy by word |
| `/weak-words` | Weak words list |
| `/word-bank` | Full word bank with filters |
