from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import List


_WORD_PROGRESS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS word_progress (
    word_id INTEGER PRIMARY KEY,
    last_reviewed TEXT,
    next_review TEXT,
    difficulty_score INTEGER NOT NULL DEFAULT 0,
    review_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(word_id) REFERENCES words(id) ON DELETE CASCADE
);
"""


def _ensure_word_progress_table(conn: sqlite3.Connection) -> None:
    """
    Makes sure the word_progress table exists.
    This is defensive in case an older DB was created before the
    schema update in database.db.init_db.
    """
    conn.executescript(_WORD_PROGRESS_SCHEMA_SQL)


def calculate_next_review(score: int) -> datetime:
    """
    Returns the next review datetime based on difficulty_score.

    Mapping (after incrementing difficulty_score on correct answer):
    0 -> 1 day
    1 -> 3 days
    2 -> 7 days
    3+ -> 14 days
    """
    if score <= 0:
        days = 1
    elif score == 1:
        days = 3
    elif score == 2:
        days = 7
    else:
        days = 14
    return datetime.now() + timedelta(days=days)


def get_due_words(
    conn: sqlite3.Connection,
    start_id: int,
    end_id: int,
) -> List[sqlite3.Row]:
    """
    Returns words between start_id and end_id whose next_review is due
    (next_review <= now OR next_review IS NULL), ordered by id.
    """
    _ensure_word_progress_table(conn)
    return list(
        conn.execute(
            """
            SELECT w.id,
                   w.character,
                   w.pinyin,
                   w.meaning,
                   w.pos
            FROM words w
            LEFT JOIN word_progress wp ON wp.word_id = w.id
            WHERE w.id BETWEEN ? AND ?
              AND (wp.next_review IS NULL OR wp.next_review <= datetime('now'))
            ORDER BY w.id
            """,
            (start_id, end_id),
        ).fetchall()
    )


def update_word_progress(
    conn: sqlite3.Connection,
    word_id: int,
    knew: bool,
) -> None:
    """
    Updates spaced-repetition metadata for a word based on whether
    the user knew the card.
    """
    _ensure_word_progress_table(conn)

    row = conn.execute(
        "SELECT difficulty_score, review_count FROM word_progress WHERE word_id = ?",
        (word_id,),
    ).fetchone()

    current_score = int(row["difficulty_score"]) if row else 0
    current_count = int(row["review_count"]) if row else 0

    now = datetime.now()

    if knew:
        new_score = current_score + 1
        next_review_dt = calculate_next_review(new_score)
    else:
        new_score = 0
        next_review_dt = now + timedelta(days=1)

    new_count = current_count + 1

    conn.execute(
        """
        INSERT INTO word_progress (word_id, last_reviewed, next_review, difficulty_score, review_count)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(word_id) DO UPDATE SET
            last_reviewed = excluded.last_reviewed,
            next_review = excluded.next_review,
            difficulty_score = excluded.difficulty_score,
            review_count = excluded.review_count
        """,
        (
            word_id,
            now.isoformat(timespec="seconds"),
            next_review_dt.isoformat(timespec="seconds"),
            new_score,
            new_count,
        ),
    )

