#!/usr/bin/env python3
"""
Reset the TOCFL platform to a fresh state: remove all users and learning/progress data.
Vocabulary (words table, loaded from Excel) and audio files are NOT touched.

Run from project root:
  python reset_database.py

After reset, the app will start with no users; new users start from Day 1 with zero progress.
Tables are recreated automatically on next app start if needed (init_db uses CREATE TABLE IF NOT EXISTS).
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Project root = parent of this script
PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "cache" / "app.db"

# Tables to clear, in dependency order (children before parents for FK safety).
# We keep: words, examples (vocabulary and cached example sentences).
TABLES_TO_CLEAR = [
    "generated_tests",  # cached test sessions
    "user_stats",       # leaderboard, streaks, accuracy
    "word_mastery",     # per-user reading/listening/writing mastery
    "weak_words",
    "user_progress",    # flashcard attempts, known, correct, etc.
    "test_results",
    "user_settings",    # start_date per user
    "users",
    "word_progress",    # spaced repetition: next_review, difficulty_score, etc.
]


def reset_database(db_path: Path) -> None:
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        print("Nothing to reset. Run the app once to create the database.")
        return

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON;")

    try:
        for table in TABLES_TO_CLEAR:
            try:
                conn.execute(f"DELETE FROM {table}")
                count = conn.total_changes
                if count:
                    print(f"  Cleared {table}: {count} row(s)")
            except sqlite3.OperationalError as e:
                # Table might not exist in older DBs
                if "no such table" in str(e).lower():
                    print(f"  Skip {table} (table does not exist)")
                else:
                    raise
        conn.commit()
        print("Reset complete. All user and progress data removed.")
        print("Kept: words, examples (vocabulary). Audio files unchanged.")
    finally:
        conn.close()


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Reset TOCFL database: remove all users and progress.")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--db", type=Path, default=DB_PATH, help=f"Path to database (default: {DB_PATH})")
    args = parser.parse_args()
    db_path = args.db.resolve()

    print("TOCFL database reset")
    print(f"Database: {db_path}")
    if not db_path.exists():
        reset_database(db_path)
        return 0

    if not args.yes:
        confirm = input("Remove all users and progress? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Aborted.")
            return 1

    reset_database(db_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
