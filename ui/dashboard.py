from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from database import models
from flashcards.flashcard_engine import StudyPlan
from progress.analytics import add_day_index, fig_test_scores, progress_summary


def render_dashboard(conn, user: models.User, plan: StudyPlan, start_date: date) -> None:
    st.title("TOCFL A1 Study Dashboard")

    progress_rows = conn.execute(
        "SELECT word_id, known, mistakes, attempts, correct FROM user_progress WHERE user_id = ?",
        (user.id,),
    ).fetchall()
    progress_df = pd.DataFrame([dict(r) for r in progress_rows]) if progress_rows else pd.DataFrame(
        columns=["word_id", "known", "mistakes", "attempts", "correct"]
    )
    summary = progress_summary(progress_df)

    st.subheader("Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Current day", plan.current_day)
    c2.metric("Words learned", f"{summary['known_words']} / 300")
    c3.metric(
        "Flashcard accuracy",
        "-" if summary["accuracy"] is None else f"{summary['accuracy']*100:.1f}%",
    )
    st.progress(min(1.0, summary["known_words"] / 300.0))

    st.subheader("Today's tasks")
    st.markdown(
        f"""
- **Flashcards**: Day {plan.current_day} (words up to **{plan.unlocked_upto_word_id}**)
- **Daily test**: 10 questions (words learned so far)
"""
    )

    st.subheader("Test scores")
    test_rows = models.list_test_results(conn, user.id)
    test_df = pd.DataFrame([dict(r) for r in test_rows]) if test_rows else pd.DataFrame(
        columns=["date", "test_type", "score", "total"]
    )
    if not test_df.empty:
        test_df = add_day_index(test_df, start_date=start_date)
    fig = fig_test_scores(test_df)
    if fig is None:
        st.info("No tests taken yet.")
    else:
        st.plotly_chart(fig, use_container_width=True)

