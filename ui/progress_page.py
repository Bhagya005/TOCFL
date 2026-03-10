from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from database import models
from flashcards.flashcard_engine import StudyPlan
from progress.analytics import (
    add_day_index,
    fig_accuracy_by_word,
    fig_test_scores,
    progress_summary,
)


def render_progress(conn, user: models.User, plan: StudyPlan, start_date: date) -> None:
    st.title("Progress")

    # Progress table
    prog_rows = conn.execute(
        "SELECT word_id, known, mistakes, attempts, correct FROM user_progress WHERE user_id = ?",
        (user.id,),
    ).fetchall()
    prog_df = pd.DataFrame([dict(r) for r in prog_rows]) if prog_rows else pd.DataFrame(
        columns=["word_id", "known", "mistakes", "attempts", "correct"]
    )
    summary = progress_summary(prog_df)

    st.subheader("Overall")
    st.metric("Words learned", f"{summary['known_words']} / 300")
    st.progress(min(1.0, summary["known_words"] / 300.0))
    if summary["accuracy"] is not None:
        st.metric("Flashcard accuracy", f"{summary['accuracy']*100:.1f}%")

    st.subheader("Test scores")
    trows = models.list_test_results(conn, user.id)
    tdf = pd.DataFrame([dict(r) for r in trows]) if trows else pd.DataFrame(
        columns=["date", "test_type", "score", "total"]
    )
    if not tdf.empty:
        tdf = add_day_index(tdf, start_date=start_date)
    fig = fig_test_scores(tdf)
    if fig is None:
        st.info("No test results yet.")
    else:
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Accuracy by word")
    wrows = conn.execute(
        """
        SELECT w.id AS word_id, w.character, COALESCE(up.attempts, 0) AS attempts, COALESCE(up.correct, 0) AS correct
        FROM words w
        LEFT JOIN user_progress up
            ON up.word_id = w.id AND up.user_id = ?
        WHERE w.id <= ?
        """,
        (user.id, plan.unlocked_upto_word_id),
    ).fetchall()
    wdf = pd.DataFrame([dict(r) for r in wrows]) if wrows else pd.DataFrame()
    fig2 = fig_accuracy_by_word(wdf, top_n=40)
    if fig2 is None:
        st.info("No flashcard data yet.")
    else:
        st.plotly_chart(fig2, use_container_width=True)

