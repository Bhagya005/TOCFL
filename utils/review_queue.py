from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional

from utils.spaced_repetition import _ensure_word_progress_table


def _id_range_clause(start_id: Optional[int], end_id: Optional[int]) -> str:
    if start_id is None or end_id is None:
        return ""
    return " AND w.id BETWEEN ? AND ? "


def get_weak_words(
    conn: sqlite3.Connection,
    user_id: int,
    limit: int,
    start_id: int | None = None,
    end_id: int | None = None,
) -> List[sqlite3.Row]:
    """
    Returns words considered "weak":
    - difficulty_score == 0  OR
    - last answer incorrect (approximated as mistakes > correct)
    within an optional ID range.
    """
    _ensure_word_progress_table(conn)
    id_clause = _id_range_clause(start_id, end_id)

    params: list[object] = [user_id]
    if id_clause:
        params.extend([start_id, end_id])
    params.append(limit)

    return list(
        conn.execute(
            f"""
            SELECT w.id,
                   w.character,
                   w.pinyin,
                   w.meaning,
                   w.pos
            FROM words w
            LEFT JOIN word_progress wp ON wp.word_id = w.id
            LEFT JOIN user_progress up
                ON up.word_id = w.id AND up.user_id = ?
            WHERE (wp.difficulty_score = 0
                   OR COALESCE(up.mistakes, 0) > COALESCE(up.correct, 0))
                  {id_clause}
            ORDER BY w.id
            LIMIT ?
            """,
            params,
        ).fetchall()
    )


def get_due_words(
    conn: sqlite3.Connection,
    limit: int,
    start_id: int | None = None,
    end_id: int | None = None,
) -> List[sqlite3.Row]:
    """
    Returns words whose next_review is due (<= now) within
    an optional ID range.
    """
    _ensure_word_progress_table(conn)
    id_clause = _id_range_clause(start_id, end_id)

    now = datetime.now().isoformat(timespec="seconds")
    params: list[object] = [now]
    if id_clause:
        params.extend([start_id, end_id])
    params.append(limit)

    return list(
        conn.execute(
            f"""
            SELECT w.id,
                   w.character,
                   w.pinyin,
                   w.meaning,
                   w.pos
            FROM words w
            JOIN word_progress wp ON wp.word_id = w.id
            WHERE wp.next_review IS NOT NULL
              AND wp.next_review <= ?
              {id_clause}
            ORDER BY wp.next_review ASC, w.id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
    )


def get_new_words(
    conn: sqlite3.Connection,
    limit: int,
    start_id: int | None = None,
    end_id: int | None = None,
) -> List[sqlite3.Row]:
    """
    Returns words that have no entry in word_progress yet
    (never reviewed), within an optional ID range.
    """
    _ensure_word_progress_table(conn)
    id_clause = _id_range_clause(start_id, end_id)

    params: list[object] = []
    if id_clause:
        params.extend([start_id, end_id])
    params.append(limit)

    return list(
        conn.execute(
            f"""
            SELECT w.id,
                   w.character,
                   w.pinyin,
                   w.meaning,
                   w.pos
            FROM words w
            LEFT JOIN word_progress wp ON wp.word_id = w.id
            WHERE wp.word_id IS NULL
              {id_clause}
            ORDER BY w.id
            LIMIT ?
            """,
            params,
        ).fetchall()
    )

