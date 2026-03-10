from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px


def progress_summary(progress_df: pd.DataFrame) -> dict:
    """
    progress_df columns: word_id, known, mistakes, attempts, correct
    """
    if progress_df.empty:
        return {"known_words": 0, "attempts": 0, "correct": 0, "accuracy": None}
    known_words = int((progress_df["known"] == 1).sum())
    attempts = int(progress_df["attempts"].sum())
    correct = int(progress_df["correct"].sum())
    accuracy = (correct / attempts) if attempts else None
    return {"known_words": known_words, "attempts": attempts, "correct": correct, "accuracy": accuracy}


def fig_test_scores(test_results_df: pd.DataFrame):
    """
    test_results_df columns: date, test_type, score, total, day_index
    """
    if test_results_df.empty:
        return None
    df = test_results_df.copy()
    df["pct"] = (df["score"] / df["total"]) * 100.0
    fig = px.line(
        df,
        x="day_index",
        y="pct",
        color="test_type",
        markers=True,
        title="Test scores vs days",
        labels={"day_index": "Study day", "pct": "Score (%)", "test_type": "Test type"},
    )
    fig.update_layout(yaxis=dict(range=[0, 100]))
    return fig


def fig_accuracy_by_word(word_stats_df: pd.DataFrame, top_n: int = 40):
    """
    word_stats_df columns: word_id, character, attempts, correct
    """
    if word_stats_df.empty:
        return None
    df = word_stats_df.copy()
    df["accuracy"] = df.apply(
        lambda r: (r["correct"] / r["attempts"]) if r["attempts"] else None, axis=1
    )
    df = df.dropna(subset=["accuracy"])
    if df.empty:
        return None
    df = df.sort_values(["accuracy", "attempts"], ascending=[True, False]).head(top_n)
    fig = px.bar(
        df,
        x="character",
        y="accuracy",
        title=f"Weakest accuracy by word (top {min(top_n, len(df))})",
        labels={"character": "Word", "accuracy": "Accuracy"},
    )
    fig.update_layout(yaxis=dict(range=[0, 1]))
    return fig


def add_day_index(test_df: pd.DataFrame, start_date: date) -> pd.DataFrame:
    if test_df.empty:
        return test_df
    df = test_df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["day_index"] = df["date"].apply(lambda d: (d - start_date).days + 1)
    return df

