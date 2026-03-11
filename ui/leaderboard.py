from __future__ import annotations

import streamlit as st

from database import models


def render_leaderboard(conn, user: models.User) -> None:
    st.title("🏆 Leaderboard")

    # Defensive: ensure stats table exists and is up to date.
    models.refresh_all_user_stats(conn)

    rows = conn.execute(
        """
        SELECT us.user_id,
               us.username,
               us.streak_days,
               us.words_learned,
               us.tests_taken,
               us.avg_test_score,
               us.total_points
        FROM user_stats us
        ORDER BY us.total_points DESC, us.username ASC
        """
    ).fetchall()

    if not rows:
        st.info("No stats available yet. Start studying to appear on the leaderboard.")
        return

    data = []
    for rank, r in enumerate(rows, start=1):
        # Recompute test stats directly from test_results to avoid any stale values.
        test_rows = models.list_test_results(conn, int(r["user_id"]))
        tests_taken = len(test_rows)
        if tests_taken > 0:
            percents: list[float] = []
            for tr in test_rows:
                total = float(tr["total"] or 0)
                score = float(tr["score"] or 0)
                if total > 0:
                    percents.append((score / total) * 100.0)
            avg_display = sum(percents) / len(percents) if percents else 0.0
        else:
            avg_display = 0.0

        data.append(
            {
                "Rank": rank,
                "User": r["username"],
                "Points": int(r["total_points"]),
                "Streak": int(r["streak_days"]),
                "Words Learned": int(r["words_learned"]),
                "Avg Test": f"{avg_display:.0f}%",
            }
        )

    st.dataframe(data, hide_index=True, width="stretch")

    st.subheader("Points comparison")

    max_points = max(d["Points"] for d in data) or 1
    for row in data:
        name = row["User"]
        pts = row["Points"]
        bar_len = max(1, int(20 * pts / max_points))
        bar = "█" * bar_len
        st.text(f"{name:<10} {bar} {pts}")

