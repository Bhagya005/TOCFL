from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


@dataclass(frozen=True)
class DBConfig:
    path: Path


def default_db_config() -> DBConfig:
    return DBConfig(path=Path("cache") / "app.db")


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_conn(cfg: DBConfig | None = None) -> Iterator[sqlite3.Connection]:
    cfg = cfg or default_db_config()
    conn = _connect(cfg.path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            start_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            character TEXT NOT NULL,
            pinyin TEXT,
            meaning TEXT,
            pos TEXT,
            category TEXT,
            subcategory TEXT
        );

        CREATE TABLE IF NOT EXISTS examples (
            word_id INTEGER PRIMARY KEY,
            sentence TEXT NOT NULL,
            pinyin TEXT NOT NULL,
            translation TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(word_id) REFERENCES words(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER NOT NULL,
            word_id INTEGER NOT NULL,
            known INTEGER NOT NULL DEFAULT 0,
            mistakes INTEGER NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 0,
            correct INTEGER NOT NULL DEFAULT 0,
            last_seen TEXT,
            PRIMARY KEY(user_id, word_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(word_id) REFERENCES words(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            test_type TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            meta_json TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS weak_words (
            user_id INTEGER NOT NULL,
            word_id INTEGER NOT NULL,
            added_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY(user_id, word_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(word_id) REFERENCES words(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS generated_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            test_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, date, test_type),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )


def db_has_words(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT COUNT(1) AS c FROM words").fetchone()
    return bool(row and row["c"] > 0)


def upsert_words(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    conn.executemany(
        """
        INSERT INTO words (id, character, pinyin, meaning, pos, category, subcategory)
        VALUES (:id, :character, :pinyin, :meaning, :pos, :category, :subcategory)
        ON CONFLICT(id) DO UPDATE SET
            character=excluded.character,
            pinyin=excluded.pinyin,
            meaning=excluded.meaning,
            pos=excluded.pos,
            category=excluded.category,
            subcategory=excluded.subcategory
        """,
        rows,
    )

