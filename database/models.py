from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


PBKDF2_ITERS = 200_000

_USER_STATS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    streak_days INTEGER NOT NULL DEFAULT 0,
    words_learned INTEGER NOT NULL DEFAULT 0,
    tests_taken INTEGER NOT NULL DEFAULT 0,
    avg_test_score REAL NOT NULL DEFAULT 0,
    total_points REAL NOT NULL DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


def ensure_user_stats_table(conn: sqlite3.Connection) -> None:
    """
    Make sure user_stats exists for older databases that predate this table.
    Safe to call multiple times.
    """
    conn.executescript(_USER_STATS_SCHEMA_SQL)


def _pbkdf2_hash_password(password: str, salt_hex: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        PBKDF2_ITERS,
    )
    return dk.hex()


def hash_password(password: str) -> str:
    salt_hex = secrets.token_hex(16)
    hashed = _pbkdf2_hash_password(password, salt_hex)
    return f"pbkdf2_sha256${PBKDF2_ITERS}${salt_hex}${hashed}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters_s, salt_hex, hashed = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iters = int(iters_s)
        cand = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), iters
        ).hex()
        return hmac.compare_digest(cand, hashed)
    except Exception:
        return False


@dataclass(frozen=True)
class User:
    id: int
    username: str


def get_user_by_username(conn: sqlite3.Connection, username: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()


def count_users(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(1) AS c FROM users").fetchone()
    return int(row["c"]) if row else 0


def create_user(conn: sqlite3.Connection, username: str, password: str) -> User:
    pw = hash_password(password)
    cur = conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, pw),
    )
    user_id = int(cur.lastrowid)
    conn.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
    # Initialize user_stats row
    ensure_user_stats_table(conn)
    conn.execute(
        """
        INSERT OR IGNORE INTO user_stats (user_id, username)
        VALUES (?, ?)
        """,
        (user_id, username),
    )
    return User(id=user_id, username=username)


def authenticate(conn: sqlite3.Connection, username: str, password: str) -> User | None:
    row = get_user_by_username(conn, username)
    if not row:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return User(id=int(row["id"]), username=str(row["username"]))


def get_or_set_start_date(conn: sqlite3.Connection, user_id: int) -> date:
    row = conn.execute(
        "SELECT start_date FROM user_settings WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row and row["start_date"]:
        return date.fromisoformat(row["start_date"])
    today = date.today()
    conn.execute(
        "INSERT INTO user_settings (user_id, start_date) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET start_date=excluded.start_date",
        (user_id, today.isoformat()),
    )
    return today


def list_words(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT id, character, pinyin, meaning, pos, category, subcategory FROM words ORDER BY id"
        ).fetchall()
    )


def get_words_range(conn: sqlite3.Connection, start_id: int, end_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT id, character, pinyin, meaning, pos FROM words WHERE id BETWEEN ? AND ? ORDER BY id",
            (start_id, end_id),
        ).fetchall()
    )


def get_words_upto(conn: sqlite3.Connection, end_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT id, character, pinyin, meaning, pos FROM words WHERE id <= ? ORDER BY id",
            (end_id,),
        ).fetchall()
    )


def get_word_by_character(conn: sqlite3.Connection, character: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, character, pinyin, meaning, pos FROM words WHERE character = ? LIMIT 1",
        (character,),
    ).fetchone()


def get_progress_map(conn: sqlite3.Connection, user_id: int) -> dict[int, dict[str, Any]]:
    rows = conn.execute(
        "SELECT word_id, known, mistakes, attempts, correct FROM user_progress WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    out: dict[int, dict[str, Any]] = {}
    for r in rows:
        out[int(r["word_id"])] = {
            "known": int(r["known"]),
            "mistakes": int(r["mistakes"]),
            "attempts": int(r["attempts"]),
            "correct": int(r["correct"]),
        }
    return out


def record_flashcard_result(conn: sqlite3.Connection, user_id: int, word_id: int, knew: bool) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO user_progress (user_id, word_id, known, mistakes, attempts, correct, last_seen)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(user_id, word_id) DO UPDATE SET
            attempts = attempts + 1,
            correct = correct + excluded.correct,
            mistakes = mistakes + excluded.mistakes,
            known = CASE
                WHEN excluded.known = 1 THEN 1
                ELSE user_progress.known
            END,
            last_seen = excluded.last_seen
        """,
        (
            user_id,
            word_id,
            1 if knew else 0,
            0 if knew else 1,
            1 if knew else 0,
            now,
        ),
    )
    if not knew:
        maybe_add_weak_word(conn, user_id, word_id)
    _update_user_stats(conn, user_id)


def maybe_add_weak_word(conn: sqlite3.Connection, user_id: int, word_id: int) -> None:
    row = conn.execute(
        "SELECT mistakes FROM user_progress WHERE user_id = ? AND word_id = ?",
        (user_id, word_id),
    ).fetchone()
    if not row:
        return
    if int(row["mistakes"]) >= 3:
        conn.execute(
            "INSERT OR IGNORE INTO weak_words (user_id, word_id) VALUES (?, ?)",
            (user_id, word_id),
        )


def list_weak_words(conn: sqlite3.Connection, user_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT w.id, w.character, w.pinyin, w.meaning, w.pos
            FROM weak_words ww
            JOIN words w ON w.id = ww.word_id
            WHERE ww.user_id = ?
            ORDER BY ww.added_at DESC, w.id ASC
            """,
            (user_id,),
        ).fetchall()
    )


def upsert_example(
    conn: sqlite3.Connection,
    word_id: int,
    sentence: str,
    pinyin: str,
    translation: str,
) -> None:
    conn.execute(
        """
        INSERT INTO examples (word_id, sentence, pinyin, translation)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(word_id) DO UPDATE SET
            sentence=excluded.sentence,
            pinyin=excluded.pinyin,
            translation=excluded.translation
        """,
        (word_id, sentence, pinyin, translation),
    )


def get_example(conn: sqlite3.Connection, word_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT word_id, sentence, pinyin, translation FROM examples WHERE word_id = ?",
        (word_id,),
    ).fetchone()


def save_test_result(
    conn: sqlite3.Connection,
    user_id: int,
    day: date,
    test_type: str,
    score: int,
    total: int,
    meta: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO test_results (user_id, date, test_type, score, total, meta_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            day.isoformat(),
            test_type,
            int(score),
            int(total),
            json.dumps(meta or {}, ensure_ascii=False),
        ),
    )
    _update_user_stats(conn, user_id)


def list_test_results(conn: sqlite3.Connection, user_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT date, test_type, score, total
            FROM test_results
            WHERE user_id = ?
            ORDER BY date ASC, id ASC
            """,
            (user_id,),
        ).fetchall()
    )


def get_latest_test_result(
    conn: sqlite3.Connection, user_id: int, test_type: str, day: date
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, score, total
        FROM test_results
        WHERE user_id = ? AND test_type = ? AND date = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id, test_type, day.isoformat()),
    ).fetchone()


def get_cached_generated_test(
    conn: sqlite3.Connection, user_id: int, day: date, test_type: str
) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT payload_json
        FROM generated_tests
        WHERE user_id = ? AND date = ? AND test_type = ?
        """,
        (user_id, day.isoformat(), test_type),
    ).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["payload_json"])
    except Exception:
        return None


def save_cached_generated_test(
    conn: sqlite3.Connection,
    user_id: int,
    day: date,
    test_type: str,
    payload: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO generated_tests (user_id, date, test_type, payload_json)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, date, test_type) DO UPDATE SET
            payload_json=excluded.payload_json
        """,
        (user_id, day.isoformat(), test_type, json.dumps(payload, ensure_ascii=False)),
    )


def delete_cached_generated_test(
    conn: sqlite3.Connection, user_id: int, day: date, test_type: str
) -> None:
    conn.execute(
        "DELETE FROM generated_tests WHERE user_id = ? AND date = ? AND test_type = ?",
        (user_id, day.isoformat(), test_type),
    )


def _ensure_user_stats_row(conn: sqlite3.Connection, user_id: int) -> None:
    ensure_user_stats_table(conn)
    row = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return
    username = str(row["username"])
    conn.execute(
        """
        INSERT INTO user_stats (user_id, username)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username
        """,
        (user_id, username),
    )


def _compute_words_learned(conn: sqlite3.Connection, user_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(1) AS c FROM user_progress WHERE user_id = ? AND known = 1",
        (user_id,),
    ).fetchone()
    return int(row["c"] or 0) if row else 0


def _compute_test_stats(conn: sqlite3.Connection, user_id: int) -> tuple[int, float]:
    """
    Returns (tests_taken, avg_test_accuracy).
    avg_test_accuracy = average of (correct_answers / total_questions) across all tests (0.0 to 1.0).
    """
    rows = conn.execute(
        "SELECT score, total FROM test_results WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    if not rows:
        return 0, 0.0
    tests_taken = len(rows)
    accuracies: list[float] = []
    for r in rows:
        total = float(r["total"] or 0)
        score = float(r["score"] or 0)
        if total > 0:
            accuracies.append(score / total)
    avg_test_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    return tests_taken, avg_test_accuracy


def _compute_streak_days(conn: sqlite3.Connection, user_id: int) -> int:
    """
    Computes number of consecutive days up to today where the user
    had any activity (flashcards or tests).
    """
    today = date.today()
    rows = conn.execute(
        """
        SELECT DISTINCT d FROM (
            SELECT date(last_seen) AS d
            FROM user_progress
            WHERE user_id = ? AND last_seen IS NOT NULL
            UNION
            SELECT date AS d
            FROM test_results
            WHERE user_id = ?
        )
        ORDER BY d DESC
        """,
        (user_id, user_id),
    ).fetchall()
    active_dates = {date.fromisoformat(str(r["d"])) for r in rows if r["d"]}
    if not active_dates:
        return 0
    streak = 0
    cur = today
    while cur in active_dates:
        streak += 1
        cur = cur.fromordinal(cur.toordinal() - 1)
    return streak


def _update_user_stats(conn: sqlite3.Connection, user_id: int) -> None:
    """
    Recalculate and persist user_stats based on current progress and tests.
    """
    ensure_user_stats_table(conn)
    _ensure_user_stats_row(conn, user_id)

    words_learned = _compute_words_learned(conn, user_id)
    tests_taken, avg_test_accuracy = _compute_test_stats(conn, user_id)
    streak_days = _compute_streak_days(conn, user_id)

    consistency_score = streak_days * 10
    learning_score = words_learned * 5
    test_score = avg_test_accuracy * tests_taken
    total_points = consistency_score + learning_score + test_score

    conn.execute(
        """
        UPDATE user_stats
        SET streak_days = ?,
            words_learned = ?,
            tests_taken = ?,
            avg_test_score = ?,
            total_points = ?
        WHERE user_id = ?
        """,
        (
            int(streak_days),
            int(words_learned),
            int(tests_taken),
            float(avg_test_accuracy),
            float(total_points),
            user_id,
        ),
    )


def refresh_all_user_stats(conn: sqlite3.Connection) -> None:
    """
    Recompute user_stats for all users from current progress and tests.
    Safe to call from UI pages before showing leaderboard.
    """
    ensure_user_stats_table(conn)
    rows = conn.execute("SELECT id FROM users").fetchall()
    for r in rows:
        _update_user_stats(conn, int(r["id"]))

