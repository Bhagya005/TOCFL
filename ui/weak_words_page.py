from __future__ import annotations

import streamlit as st

from ai.sentence_generator import get_or_create_example
from audio.embed import safe_mp3_data_uri
from audio.tts import tts_to_mp3_path
from database import models
from ui.components.flashcard_card import render_flashcard_card
from utils.pinyin import numbers_to_tone_marks


def render_weak_words(conn, user: models.User) -> None:
    st.title("Weak Words")

    weak = models.list_weak_words(conn, user.id)
    if not weak:
        st.info("No weak words yet. A word becomes weak after 3 mistakes.")
        return

    st.subheader("Your weak words")
    st.dataframe(
        [{"id": int(r["id"]), "character": r["character"], "pinyin": r["pinyin"], "meaning": r["meaning"], "pos": r["pos"]} for r in weak],
        hide_index=True,
        width="stretch",
    )

    st.divider()
    st.subheader("Practice weak words (flashcards)")

    if "weak_idx" not in st.session_state or st.button("Restart practice"):
        st.session_state["weak_idx"] = 0
        st.session_state["weak_flipped"] = False

    idx = int(st.session_state.get("weak_idx", 0))
    idx = max(0, min(idx, len(weak) - 1))
    st.session_state["weak_idx"] = idx

    w = weak[idx]
    word_id = int(w["id"])
    char = str(w["character"])
    pinyin = numbers_to_tone_marks(str(w["pinyin"] or ""))
    meaning = str(w["meaning"] or "")

    st.caption(f"Card {idx + 1} / {len(weak)}")

    ex = get_or_create_example(conn, word_id=word_id, word=char, pinyin=pinyin, meaning=meaning)
    flipped = bool(st.session_state.get("weak_flipped", False))

    char_audio_uri = safe_mp3_data_uri(tts_to_mp3_path(char, lang="zh-CN")) if flipped else None

    render_flashcard_card(
        flipped=flipped,
        character=char,
        pinyin=pinyin,
        meaning=meaning,
        example_cn=ex.chinese,
        example_py=ex.pinyin,
        example_en=ex.english,
        word_audio_uri=char_audio_uri,
        height=440,
    )

    pad_l, mid, pad_r = st.columns([1, 6, 1])
    with mid:
        b1, b2, b3 = st.columns([1, 1, 1])
        with b1:
            if st.button("Flip", type="secondary", width="stretch"):
                st.session_state["weak_flipped"] = not flipped
                st.rerun()
        with b2:
            if st.button("I knew this", type="primary", width="stretch"):
                models.record_flashcard_result(conn, user.id, word_id, knew=True)
                _advance(len(weak))
        with b3:
            if st.button("I didn't know", width="stretch"):
                models.record_flashcard_result(conn, user.id, word_id, knew=False)
                _advance(len(weak))


def _advance(total: int) -> None:
    st.session_state["weak_flipped"] = False
    st.session_state["weak_idx"] = min(total - 1, int(st.session_state.get("weak_idx", 0)) + 1)
    st.rerun()

    # Card rendering is handled by ui.components.flashcard_card now.


