# AI-powered TOCFL A1 Study Dashboard

Local multi-user Streamlit dashboard for studying the first 300 TOCFL A1 vocabulary words from `CCCC_Vocabulary_2022.xlsx`, with flashcards, AI example sentences, AI-assisted tests, and progress tracking.

## Setup

### 1) Create a virtual environment (recommended)

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment variables

- Copy `.env.example` to `.env`
- Set:
  - `OPENAI_API_KEY` (optional but recommended)
  - `OPENAI_MODEL` (optional, default: `gpt-4o-mini`)

If `OPENAI_API_KEY` is not set, the app will still run, using offline fallbacks for distractors and example sentences.

### 4) Put the Excel file in the project root

Keep this file in the same folder as `app.py`:

- `CCCC_Vocabulary_2022.xlsx`

### 5) Run the app

```bash
streamlit run app.py
```

## Login / multi-user

- You can create up to **2 users** from the login screen (until the limit is reached).
- Each user has independent progress, test scores, and weak words.

## Data & caching

- SQLite DB is stored at `cache/app.db`
- Audio is cached at `cache/audio/`
- OpenAI results are cached in SQLite (example sentences) to avoid repeated calls.

## Streamlit Cloud

1. Push this project to GitHub
2. In Streamlit Cloud, set **Secrets**:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (optional)
3. Ensure `CCCC_Vocabulary_2022.xlsx` is included in the repo (or adapt the loader to fetch from remote storage).

