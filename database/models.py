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

