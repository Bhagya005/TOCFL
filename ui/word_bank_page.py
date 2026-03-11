from __future__ import annotations

import pandas as pd
import streamlit as st

from database import models


def render_word_bank(conn, user: models.User) -> None:
    st.title("Word Bank")

    words = models.list_words(conn)
    if not words:
        st.error("No words found. Make sure the Excel file loaded correctly.")
        return

    progress = models.get_progress_map(conn, user.id)
    weak = {int(r["id"]) for r in models.list_weak_words(conn, user.id)}

    rows = []
    for w in words:
        wid = int(w["id"])
        p = progress.get(wid, {"known": 0, "mistakes": 0, "attempts": 0, "correct": 0})
        rows.append(
            {
                "id": wid,
                "character": w["character"],
                "pinyin": w["pinyin"],
                "meaning": w["meaning"],
                "pos": w["pos"],
                "learned": bool(p["known"]),
                "weak": wid in weak,
                "mistakes": int(p["mistakes"]),
                "attempts": int(p["attempts"]),
            }
        )

    df = pd.DataFrame(rows)

    st.subheader("Filters")
    search = st.text_input("Search (character / pinyin / meaning)").strip()
    c1, c2, c3 = st.columns(3)
    with c1:
        show_learned = st.checkbox("Learned", value=True)
    with c2:
        show_unlearned = st.checkbox("Unlearned", value=True)
    with c3:
        show_weak = st.checkbox("Weak only", value=False)

    out = df.copy()
    if search:
        mask = (
            out["character"].astype(str).str.contains(search, case=False, na=False)
            | out["pinyin"].astype(str).str.contains(search, case=False, na=False)
            | out["meaning"].astype(str).str.contains(search, case=False, na=False)
        )
        out = out[mask]

    if not (show_learned and show_unlearned):
        if show_learned:
            out = out[out["learned"] == True]  # noqa: E712
        elif show_unlearned:
            out = out[out["learned"] == False]  # noqa: E712
        else:
            out = out.iloc[0:0]

    if show_weak:
        out = out[out["weak"] == True]  # noqa: E712

    st.subheader("Vocabulary")
    st.dataframe(
        out.sort_values(["id"]).reset_index(drop=True),
        hide_index=True,
        width="stretch",
    )

