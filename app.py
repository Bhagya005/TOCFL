from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from data.vocab_loader import load_vocab_first_300
from database.db import init_db
from database import models
from ai.sentence_generator import get_or_create_example
from flashcards.flashcard_engine import compute_study_plan, day_word_range, week_word_upto
from tests.daily_test import build_daily_test
from tests.weekly_test import build_weekly_test
from tests.final_test import build_final_test
from ui.dashboard import render_dashboard
from ui.flashcards_page import render_flashcards
from ui.progress_page import render_progress
from ui.weak_words_page import render_weak_words
from ui.word_bank_page import render_word_bank
from ui.tests_page import render_test_page
from ui.leaderboard import render_leaderboard


APP_TITLE = "TOCFL A1 Study Dashboard"
EXCEL_FILE = "CCCC_Vocabulary_2022.xlsx"
DB_PATH = Path("cache") / "app.db"


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title=APP_TITLE, layout="wide")

    conn = get_db()
    _ensure_vocab_loaded(conn)

    st.sidebar.title("Navigation")

    user = _require_login(conn)
    start_date = models.get_or_set_start_date(conn, user.id)
    plan = compute_study_plan(start_date=start_date, today=date.today())

    page = st.sidebar.radio(
        "Go to",
        [
            "Dashboard",
            "Today's Flashcards",
            "Daily Test",
            "Weekly Test",
            "Final Test",
            "Weak Words",
            "Leaderboard",
            "Word Bank",
            "Progress",
        ],
    )

    st.sidebar.divider()
    st.sidebar.caption(f"Logged in as: **{user.username}**")
    if st.sidebar.button("Log out"):
        st.session_state.pop("user", None)
        st.session_state["logged_in"] = False
        st.session_state["last_activity"] = None
        st.rerun()

    if page == "Dashboard":
        render_dashboard(conn, user, plan, start_date)
    elif page == "Today's Flashcards":
        render_flashcards(conn, user, plan)
    elif page == "Daily Test":
        dstart, dend = day_word_range(plan.current_day)
        todays_rows = models.get_words_range(conn, dstart, dend)
        eligible = _words_as_dicts(todays_rows)
        eligible = _enrich_with_cached_examples(conn, eligible)
        # Boost weak words in the daily test pool.
        weak_ids = {int(w["id"]) for w in models.list_weak_words(conn, user.id)}
        boosted = list(eligible)
        for w in eligible:
            if int(w["id"]) in weak_ids:
                boosted.append(w)
                boosted.append(w)
        for r in todays_rows:
            wid = int(r["id"])
            ex = get_or_create_example(
                conn,
                word_id=wid,
                word=str(r["character"]),
                pinyin=str(r["pinyin"] or ""),
                meaning=str(r["meaning"] or ""),
                pos=str(r["pos"] or ""),
            )
            for w in boosted:
                if int(w["id"]) == wid:
                    w["example_sentence"] = ex.chinese
                    w["example_translation"] = ex.english
                    break
        seed = _daily_seed(user.id)
        render_test_page(
            conn,
            user,
            title="Daily Test (40 questions)",
            test_type="daily",
            build_questions=build_daily_test,
            eligible_words=boosted,
            seed=seed,
        )
    elif page == "Weekly Test":
        if plan.current_day < 7:
            st.title("Weekly Test")
            st.info("Weekly tests unlock on Day 7, Day 14, and Day 20.")
        else:
            upto = week_word_upto(plan.current_day)
            eligible = _words_as_dicts(models.get_words_upto(conn, upto))
            eligible = _enrich_with_cached_examples(conn, eligible)
            weak_ids = {int(w["id"]) for w in models.list_weak_words(conn, user.id)}
            boosted = list(eligible)
            for w in eligible:
                if int(w["id"]) in weak_ids:
                    boosted.append(w)
                    boosted.append(w)
            seed = _daily_seed(user.id) + 7
            render_test_page(
                conn,
                user,
                title="Weekly Test (120 questions)",
                test_type="weekly",
                build_questions=build_weekly_test,
                eligible_words=boosted,
                seed=seed,
            )
    elif page == "Final Test":
        if plan.current_day < 20:
            st.title("Final Test")
            st.info("Final test unlocks on Day 20.")
        else:
            eligible = _words_as_dicts(models.get_words_upto(conn, 300))
            eligible = _enrich_with_cached_examples(conn, eligible)
            weak_ids = {int(w["id"]) for w in models.list_weak_words(conn, user.id)}
            boosted = list(eligible)
            for w in eligible:
                if int(w["id"]) in weak_ids:
                    boosted.append(w)
                    boosted.append(w)
            seed = _daily_seed(user.id) + 20
            render_test_page(
                conn,
                user,
                title="Final Test (200 questions)",
                test_type="final",
                build_questions=build_final_test,
                eligible_words=boosted,
                seed=seed,
            )
    elif page == "Weak Words":
        render_weak_words(conn, user)
    elif page == "Leaderboard":
        render_leaderboard(conn, user)
    elif page == "Word Bank":
        render_word_bank(conn, user)
    elif page == "Progress":
        render_progress(conn, user, plan, start_date)


@st.cache_resource
def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    init_db(conn)
    return conn


def _ensure_vocab_loaded(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(1) AS c FROM words").fetchone()
    if row and int(row["c"]) >= 300:
        return

    excel_path = Path(EXCEL_FILE)
    if not excel_path.exists():
        st.error(
            f"Missing `{EXCEL_FILE}` in the project root.\n\n"
            f"Put the Excel file next to `app.py` and refresh."
        )
        st.stop()

    vocab = load_vocab_first_300(excel_path)
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
        [
            (
                v.id,
                v.character,
                v.pinyin,
                v.meaning,
                v.pos,
                v.category,
                v.subcategory,
            )
            for v in vocab
        ],
    )
    conn.commit()


def _require_login(conn: sqlite3.Connection) -> models.User:
    # Inactivity timeout (20 minutes).
    timeout = timedelta(minutes=20)

    user = st.session_state.get("user")
    logged_in = bool(st.session_state.get("logged_in", False))
    last_activity_raw = st.session_state.get("last_activity")

    now = datetime.utcnow()

    # Parse last activity if present.
    last_activity = None
    if isinstance(last_activity_raw, str):
        try:
            last_activity = datetime.fromisoformat(last_activity_raw)
        except Exception:
            last_activity = None

    # If we have a logged-in user, decide based on inactivity timeout.
    if user and logged_in:
        # If we don't have a valid last_activity yet, treat this as active now.
        if last_activity is None:
            st.session_state["last_activity"] = now.isoformat()
            return user
        # Check inactivity window.
        if now - last_activity <= timeout:
            st.session_state["last_activity"] = now.isoformat()
            return user
        # Session expired due to inactivity.
        st.session_state.pop("user", None)
        st.session_state["logged_in"] = False
        st.session_state["last_activity"] = None
        st.session_state["session_expired"] = True

    st.title("Login")
    st.caption("Create up to 2 users. Each user has separate progress.")

    if st.session_state.get("session_expired"):
        st.warning("Session expired due to inactivity. Please log in again.")
        st.session_state["session_expired"] = False

    tab1, tab2 = st.tabs(["Log in", "Create user"])

    with tab1:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log in", type="primary")
        if submit:
            user = models.authenticate(conn, username.strip(), password)
            if not user:
                st.error("Invalid username or password.")
            else:
                st.session_state["user"] = user
                st.session_state["logged_in"] = True
                st.session_state["last_activity"] = datetime.utcnow().isoformat()
                st.rerun()

    with tab2:
        if models.count_users(conn) >= 2:
            st.info("User limit reached (2 users).")
        else:
            with st.form("create_user_form", clear_on_submit=True):
                new_username = st.text_input("New username")
                new_password = st.text_input("New password", type="password")
                submit2 = st.form_submit_button("Create user", type="primary")
            if submit2:
                u = new_username.strip()
                if not u or not new_password:
                    st.error("Username and password are required.")
                else:
                    try:
                        user = models.create_user(conn, u, new_password)
                        st.success("User created. You can now log in.")
                    except Exception:
                        st.error("Could not create user. Username might already exist.")

    st.stop()


def _words_as_dicts(rows) -> list[dict]:
    return [
        {"id": int(r["id"]), "character": r["character"], "pinyin": r["pinyin"], "meaning": r["meaning"]}
        for r in rows
    ]


def _enrich_with_cached_examples(conn: sqlite3.Connection, word_dicts: list[dict]) -> list[dict]:
    """
    Adds optional keys: example_sentence, example_translation
    (Only from DB cache; does not call OpenAI.)
    """
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


if __name__ == "__main__":
    main()

