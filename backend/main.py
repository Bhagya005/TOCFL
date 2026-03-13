"""
FastAPI backend for TOCFL A1 Study.
All learning logic (DB, tests, flashcards, progress) stays in Python.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

# Add project root to path so we can import from database, etc.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import init_db
from database import models
from data.vocab_loader import load_vocab_first_300
from flashcards.flashcard_engine import compute_study_plan, day_word_range, week_word_upto
from ai.sentence_generator import get_or_create_example
from utils.review_queue import get_due_words as rq_get_due_words
from utils.review_queue import get_new_words as rq_get_new_words
from utils.review_queue import get_weak_words as rq_get_weak_words
from utils.spaced_repetition import update_word_progress
from utils.pinyin import numbers_to_tone_marks
from progress.analytics import add_day_index, progress_summary

# Test builders
from tests.daily_test import build_daily_test
from tests.weekly_test import build_weekly_test
from tests.final_test import build_final_test

try:
    from fastapi import FastAPI
except ImportError:
    raise ImportError("Install fastapi and uvicorn: pip install fastapi uvicorn")

# Optional JWT (use simple token if PyJWT not installed)
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DB_PATH = PROJECT_ROOT / "cache" / "app.db"
EXCEL_FILE = PROJECT_ROOT / "CCCC_Vocabulary_2022.xlsx"
JWT_SECRET = os.getenv("JWT_SECRET", "tocfl-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"

app = FastAPI(title="TOCFL A1 API")

# Allow frontend from localhost and local network (e.g. http://192.168.8.9:3000)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]
# Optional: allow any origin matching local IP on port 3000 (for same-machine access via IP)
_app_origins = os.getenv("CORS_ORIGINS", "").strip()
if _app_origins:
    CORS_ORIGINS.extend(o.strip() for o in _app_origins.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    init_db(conn)
    return conn


def ensure_vocab(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(1) AS c FROM words").fetchone()
    if row and int(row["c"]) >= 300:
        return
    if not EXCEL_FILE.exists():
        return
    vocab = load_vocab_first_300(EXCEL_FILE)
    conn.executemany(
        """
        INSERT INTO words (id, character, pinyin, meaning, pos, category, subcategory)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            character=excluded.character,
            pinyin=excluded.pinyin,
            meaning=excluded.meaning,
            pos=excluded.pos,
            category=excluded.category,
            subcategory=excluded.subcategory
        """,
        [(v.id, v.character, v.pinyin, v.meaning, v.pos, v.category, v.subcategory) for v in vocab],
    )
    conn.commit()


def _encode_token(user_id: int, username: str) -> str:
    if JWT_AVAILABLE:
        import jwt
        return jwt.encode(
            {"sub": str(user_id), "username": username},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
    return f"{user_id}:{username}"


def _decode_token(token: str) -> tuple[int, str] | None:
    if JWT_AVAILABLE:
        try:
            import jwt
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return int(payload["sub"]), payload.get("username", "")
        except Exception:
            return None
    if ":" in token:
        a, b = token.split(":", 1)
        try:
            return int(a), b
        except ValueError:
            return None
    return None


def get_current_user(
    conn: sqlite3.Connection = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> models.User:
    ensure_vocab(conn)
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    decoded = _decode_token(creds.credentials)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, username = decoded
    row = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return models.User(id=int(row["id"]), username=str(row["username"]))


# --- Pydantic schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class FlashcardAnswerRequest(BaseModel):
    word_id: int
    knew: bool


class TestSubmitRequest(BaseModel):
    test_type: str
    answers: dict[str, Any]  # index -> int (MCQ) or str (writing)


def _words_as_dicts(rows) -> list[dict]:
    return [
        {"id": int(r["id"]), "character": r["character"], "pinyin": r["pinyin"], "meaning": r["meaning"]}
        for r in rows
    ]


def _enrich_with_cached_examples(conn: sqlite3.Connection, word_dicts: list[dict]) -> list[dict]:
    if not word_dicts:
        return word_dicts
    ids = [int(w["id"]) for w in word_dicts]
    placeholders = ",".join(["?"] * len(ids))
    rows = conn.execute(
        f"SELECT word_id, sentence, translation FROM examples WHERE word_id IN ({placeholders})",
        ids,
    ).fetchall()
    ex_map = {int(r["word_id"]): (str(r["sentence"]), str(r["translation"])) for r in rows}
    for w in word_dicts:
        wid = int(w["id"])
        if wid in ex_map:
            s, t = ex_map[wid]
            w["example_sentence"] = s
            w["example_translation"] = t
    return word_dicts


def _daily_seed(user_id: int) -> int:
    return int(date.today().strftime("%Y%m%d")) + int(user_id) * 997


# --- Auth ---

@app.post("/api/auth/login")
def login(req: LoginRequest, conn: sqlite3.Connection = Depends(get_db)):
    ensure_vocab(conn)
    user = models.authenticate(conn, req.username.strip(), req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = _encode_token(user.id, user.username)
    return {"token": token, "user": {"id": user.id, "username": user.username}}


@app.post("/api/auth/register")
def register(req: RegisterRequest, conn: sqlite3.Connection = Depends(get_db)):
    ensure_vocab(conn)
    if models.count_users(conn) >= 5:
        raise HTTPException(status_code=400, detail="User limit reached (5 users).")
    u = req.username.strip()
    if not u or not req.password:
        raise HTTPException(status_code=400, detail="Username and password required")
    try:
        user = models.create_user(conn, u, req.password)
        conn.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Username may already exist")
    token = _encode_token(user.id, user.username)
    return {"token": token, "user": {"id": user.id, "username": user.username}} 


@app.get("/api/me")
def me(user: models.User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username}


# --- Dashboard ---

@app.get("/api/dashboard")
def dashboard(
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    start_date = models.get_or_set_start_date(conn, user.id)
    conn.commit()
    plan = compute_study_plan(start_date=start_date, today=date.today())
    progress_rows = conn.execute(
        "SELECT word_id, known, mistakes, attempts, correct FROM user_progress WHERE user_id = ?",
        (user.id,),
    ).fetchall()
    progress_df = pd.DataFrame([dict(r) for r in progress_rows]) if progress_rows else pd.DataFrame(
        columns=["word_id", "known", "mistakes", "attempts", "correct"]
    )
    summary = progress_summary(progress_df)
    test_rows = models.list_test_results(conn, user.id)
    test_list = [dict(r) for r in test_rows] if test_rows else []
    test_df = pd.DataFrame(test_list) if test_list else pd.DataFrame(columns=["date", "test_type", "score", "total"])
    if not test_df.empty:
        test_df = add_day_index(test_df, start_date=start_date)
        test_list = test_df.to_dict("records")
    else:
        test_list = []
    return {
        "plan": {"current_day": plan.current_day, "unlocked_upto_word_id": plan.unlocked_upto_word_id},
        "start_date": start_date.isoformat(),
        "summary": {
            "known_words": summary["known_words"],
            "attempts": summary["attempts"],
            "correct": summary["correct"],
            "accuracy": summary["accuracy"],
        },
        "test_results": test_list,
    }


# --- Flashcards ---

@app.get("/api/flashcards/today")
def flashcards_today(
    day: int = 1,
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    start_id, end_id = day_word_range(max(1, min(20, day)))
    weak_words = rq_get_weak_words(conn, user.id, limit=300, start_id=start_id, end_id=end_id)
    due_words = rq_get_due_words(conn, limit=300, start_id=start_id, end_id=end_id)
    new_words = rq_get_new_words(conn, limit=300, start_id=start_id, end_id=end_id)
    total_weak = len(rq_get_weak_words(conn, user.id, limit=300))
    total_due = len(rq_get_due_words(conn, limit=300))
    total_new = len(rq_get_new_words(conn, limit=300))
    session_order = {}
    for group in (weak_words, due_words, new_words):
        for row in group:
            wid = int(row["id"])
            if wid not in session_order:
                session_order[wid] = row
    words = list(session_order.values())
    words_dict = _words_as_dicts(words)
    # Enrich with examples for first 20 for display
    for r in words[:20]:
        wid = int(r["id"])
        ex = get_or_create_example(
            conn,
            word_id=wid,
            word=str(r["character"]),
            pinyin=str(r["pinyin"] or ""),
            meaning=str(r["meaning"] or ""),
            pos=str(r["pos"] or ""),
        )
        for w in words_dict:
            if int(w["id"]) == wid:
                w["example_sentence"] = ex.chinese
                w["example_translation"] = ex.english
                w["example_pinyin"] = ex.pinyin
                break
    conn.commit()
    return {
        "words": words_dict,
        "total_due": total_due,
        "total_new": total_new,
        "total_weak": total_weak,
        "start_id": start_id,
        "end_id": end_id,
        "day": day,
    }


@app.post("/api/flashcards/answer")
def flashcard_answer(
    req: FlashcardAnswerRequest,
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    update_word_progress(conn, req.word_id, knew=req.knew)
    models.record_flashcard_result(conn, user.id, req.word_id, knew=req.knew)
    conn.commit()
    return {"ok": True}


# --- Tests ---

def _get_eligible_and_builder(conn, plan, user_id, test_type):
    today = date.today()
    seed_base = _daily_seed(user_id)
    if test_type == "daily":
        dstart, dend = day_word_range(plan.current_day)
        rows = models.get_words_range(conn, dstart, dend)
        eligible = _words_as_dicts(rows)
        eligible = _enrich_with_cached_examples(conn, eligible)
        for r in rows:
            wid = int(r["id"])
            ex = get_or_create_example(
                conn, word_id=wid,
                word=str(r["character"]), pinyin=str(r["pinyin"] or ""),
                meaning=str(r["meaning"] or ""), pos=str(r["pos"] or ""),
            )
            for w in eligible:
                if int(w["id"]) == wid:
                    w["example_sentence"] = ex.chinese
                    w["example_translation"] = ex.english
                    break
        return eligible, build_daily_test, seed_base, True, None
    if test_type == "weekly":
        if plan.current_day < 7:
            return [], None, None, False, "Weekly tests unlock on Day 7, Day 14, and Day 20."
        upto = week_word_upto(plan.current_day)
        eligible = _words_as_dicts(models.get_words_upto(conn, upto))
        eligible = _enrich_with_cached_examples(conn, eligible)
        return eligible, build_weekly_test, seed_base + 7, True, None
    if test_type == "final":
        if plan.current_day < 20:
            return [], None, None, False, "Final test unlocks on Day 20."
        eligible = _words_as_dicts(models.get_words_upto(conn, 300))
        eligible = _enrich_with_cached_examples(conn, eligible)
        return eligible, build_final_test, seed_base + 20, True, None
    return [], None, None, False, "Unknown test type"


@app.get("/api/tests/eligible")
def tests_eligible(
    test_type: str,
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    start_date = models.get_or_set_start_date(conn, user.id)
    plan = compute_study_plan(start_date=start_date, today=date.today())
    eligible, builder, seed, can_start, message = _get_eligible_and_builder(conn, plan, user.id, test_type)
    if not can_start:
        return {"can_start": False, "message": message, "eligible": []}
    return {"can_start": True, "eligible": eligible, "seed": seed, "test_type": test_type}


@app.post("/api/tests/start")
def tests_start(
    body: dict,
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    test_type = body.get("test_type", "daily")
    start_date = models.get_or_set_start_date(conn, user.id)
    plan = compute_study_plan(start_date=start_date, today=date.today())
    eligible, builder, seed, can_start, message = _get_eligible_and_builder(conn, plan, user.id, test_type)
    if not can_start or not builder:
        raise HTTPException(status_code=400, detail=message or "Cannot start test")
    today = date.today()
    cached = models.get_cached_generated_test(conn, user.id, today, test_type)
    if cached and cached.get("questions"):
        questions = cached["questions"]
    else:
        questions = [dict(q) for q in builder(eligible, seed)]
        models.save_cached_generated_test(conn, user.id, today, test_type, {"questions": questions})
    conn.commit()
    return {"questions": questions}


@app.post("/api/tests/submit")
def tests_submit(
    req: TestSubmitRequest,
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    today = date.today()
    cached = models.get_cached_generated_test(conn, user.id, today, req.test_type)
    if not cached or not cached.get("questions"):
        raise HTTPException(status_code=400, detail="No test in progress")
    questions = cached["questions"]
    answers = {int(k): v for k, v in req.answers.items()}

    total = len(questions)
    meaning_correct = listening_correct = writing_correct = 0
    meaning_total = listening_total = writing_total = 0
    review_rows = []

    for i, q in enumerate(questions):
        section = q.get("section", "meaning")
        user_ans = answers.get(i)
        if section == "meaning":
            meaning_total += 1
            options = q.get("options", [])
            correct_idx = int(q.get("answer_index", -1))
            correct_text = options[correct_idx] if 0 <= correct_idx < len(options) else ""
            user_text = options[user_ans] if isinstance(user_ans, int) and 0 <= user_ans < len(options) else "(no answer)"
            is_correct = isinstance(user_ans, int) and int(user_ans) == correct_idx
            if is_correct:
                meaning_correct += 1
            review_rows.append({
                "Q#": i + 1, "Section": "Meaning",
                "Question": str(q.get("prompt", "")),
                "Your answer": user_text, "Correct answer": correct_text,
                "Result": "Correct" if is_correct else "Incorrect",
            })
        elif section == "listening":
            listening_total += 1
            options = q.get("options", [])
            correct_idx = int(q.get("answer_index", -1))
            correct_text = options[correct_idx] if 0 <= correct_idx < len(options) else ""
            user_text = options[user_ans] if isinstance(user_ans, int) and 0 <= user_ans < len(options) else "(no answer)"
            is_correct = isinstance(user_ans, int) and int(user_ans) == correct_idx
            if is_correct:
                listening_correct += 1
            display_cn = str(q.get("display_cn", "")).strip()
            display_py = str(q.get("display_py", "")).strip()
            question_text = f"{display_cn} ({display_py})" if (display_cn and display_py) else display_cn or "(listening)"
            review_rows.append({
                "Q#": i + 1, "Section": "Listening",
                "Question": question_text,
                "Your answer": user_text, "Correct answer": correct_text,
                "Result": "Correct" if is_correct else "Incorrect",
            })
        else:
            writing_total += 1
            correct_pinyin_numbers = str(q.get("correct_pinyin_numbers", "")).strip()
            correct_pinyin_display = str(q.get("correct_pinyin_display", "")).strip()
            user_text = user_ans if isinstance(user_ans, str) and str(user_ans).strip() else "(no answer)"
            user_raw = str(user_ans).strip().lower().replace(" ", "") if isinstance(user_ans, str) else ""
            correct_raw = correct_pinyin_numbers.strip().lower().replace(" ", "")
            is_correct = bool(user_raw and correct_raw and user_raw == correct_raw)
            if is_correct:
                writing_correct += 1
            review_rows.append({
                "Q#": i + 1, "Section": "Writing",
                "Question": f"English: {q.get('prompt', '')}",
                "Your answer": user_text,
                "Correct answer": correct_pinyin_display or correct_pinyin_numbers,
                "Result": "Correct" if is_correct else "Incorrect",
            })

    total_correct = meaning_correct + listening_correct + writing_correct
    accuracy_percent = (100.0 * total_correct / total) if total else 0.0
    already = models.get_latest_test_result(conn, user.id, req.test_type, today)
    if not already:
        meta = {
            "version": 2,
            "meaning_score": meaning_correct, "listening_score": listening_correct,
            "writing_score": writing_correct, "accuracy_percent": round(accuracy_percent, 1),
        }
        models.save_test_result(conn, user.id, today, req.test_type, score=total_correct, total=total, meta=meta)
    conn.commit()
    return {
        "total_correct": total_correct,
        "total": total,
        "accuracy_percent": accuracy_percent,
        "meaning_score": meaning_correct,
        "meaning_total": meaning_total,
        "listening_score": listening_correct,
        "listening_total": listening_total,
        "writing_score": writing_correct,
        "writing_total": writing_total,
        "review_rows": review_rows,
        "already_completed": bool(already),
    }


# --- Audio (TTS) ---

@app.get("/api/audio")
def audio(text: str, conn: sqlite3.Connection = Depends(get_db)):
    ensure_vocab(conn)
    from audio.tts import tts_to_mp3_path
    path = tts_to_mp3_path(text or "", lang="zh-CN")
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Audio not available")
    return Response(content=path.read_bytes(), media_type="audio/mpeg")


# --- Leaderboard ---

@app.get("/api/leaderboard")
def leaderboard(
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    models.refresh_all_user_stats(conn)
    conn.commit()
    rows = conn.execute(
        """
        SELECT us.user_id, us.username, us.streak_days, us.words_learned,
               us.tests_taken, us.avg_test_score, us.total_points
        FROM user_stats us
        ORDER BY us.total_points DESC, us.username ASC
        """
    ).fetchall()
    data = []
    for rank, r in enumerate(rows, start=1):
        test_rows = models.list_test_results(conn, int(r["user_id"]))
        tests_taken = len(test_rows)
        if tests_taken > 0:
            percents = [(float(tr["score"]) / float(tr["total"]) * 100.0) for tr in test_rows if tr["total"]]
            avg_display = sum(percents) / len(percents) if percents else 0.0
        else:
            avg_display = 0.0
        data.append({
            "rank": rank,
            "user": r["username"],
            "points": int(r["total_points"]),
            "streak": int(r["streak_days"]),
            "words_learned": int(r["words_learned"]),
            "avg_test": f"{avg_display:.0f}%",
        })
    return {"leaderboard": data}


# --- Progress ---

@app.get("/api/progress")
def progress(
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    start_date = models.get_or_set_start_date(conn, user.id)
    plan = compute_study_plan(start_date=start_date, today=date.today())
    progress_rows = conn.execute(
        "SELECT word_id, known, mistakes, attempts, correct FROM user_progress WHERE user_id = ?",
        (user.id,),
    ).fetchall()
    progress_df = pd.DataFrame([dict(r) for r in progress_rows]) if progress_rows else pd.DataFrame(
        columns=["word_id", "known", "mistakes", "attempts", "correct"]
    )
    summary = progress_summary(progress_df)
    test_rows = models.list_test_results(conn, user.id)
    test_list = [dict(r) for r in test_rows] if test_rows else []
    test_df = pd.DataFrame(test_list) if test_list else pd.DataFrame(columns=["date", "test_type", "score", "total"])
    if not test_df.empty:
        test_df = add_day_index(test_df, start_date=start_date)
        test_list = test_df.to_dict("records")
    wrows = conn.execute(
        """
        SELECT w.id AS word_id, w.character, COALESCE(up.attempts, 0) AS attempts, COALESCE(up.correct, 0) AS correct
        FROM words w
        LEFT JOIN user_progress up ON up.word_id = w.id AND up.user_id = ?
        WHERE w.id <= ?
        """,
        (user.id, plan.unlocked_upto_word_id),
    ).fetchall()
    word_stats = [dict(r) for r in wrows] if wrows else []
    return {
        "plan": {"current_day": plan.current_day, "unlocked_upto_word_id": plan.unlocked_upto_word_id},
        "start_date": start_date.isoformat(),
        "summary": {"known_words": summary["known_words"], "accuracy": summary["accuracy"]},
        "test_results": test_list,
        "word_stats": word_stats,
    }


# --- Weak words ---

@app.get("/api/weak-words")
def weak_words(
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    weak = models.list_weak_words(conn, user.id)
    return {"words": [{"id": int(r["id"]), "character": r["character"], "pinyin": r["pinyin"], "meaning": r["meaning"], "pos": r["pos"]} for r in weak]}


# --- Word bank ---

@app.get("/api/word-bank")
def word_bank(
    conn: sqlite3.Connection = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    ensure_vocab(conn)
    words = models.list_words(conn)
    progress = models.get_progress_map(conn, user.id)
    weak = {int(r["id"]) for r in models.list_weak_words(conn, user.id)}
    rows = []
    for w in words:
        wid = int(w["id"])
        p = progress.get(wid, {"known": 0, "mistakes": 0, "attempts": 0, "correct": 0})
        rows.append({
            "id": wid,
            "character": w["character"],
            "pinyin": w["pinyin"],
            "meaning": w["meaning"],
            "pos": w["pos"],
            "learned": bool(p["known"]),
            "weak": wid in weak,
            "mistakes": int(p["mistakes"]),
            "attempts": int(p["attempts"]),
        })
    return {"words": rows}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
