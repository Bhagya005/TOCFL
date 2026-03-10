from __future__ import annotations

from datetime import date

import streamlit as st

from ai.sentence_generator import get_or_create_example
from ai.image_generator import get_or_create_word_image
from audio.embed import safe_mp3_data_uri, safe_png_data_uri
from audio.tts import tts_to_mp3_path
from database import models
from flashcards.flashcard_engine import StudyPlan, day_word_range
from ui.components.flashcard_card import render_flashcard_card
from utils.pinyin import numbers_to_tone_marks
from utils.fallback_image import fallback_image_data_uri


def render_flashcards(conn, user: models.User, plan: StudyPlan) -> None:
    st.title("Today's Flashcards")

    day = st.number_input(
        "Select day",
        min_value=1,
        max_value=20,
        value=int(st.session_state.get("flashcard_day", plan.current_day)),
        step=1,
        help="You can review previous days too.",
    )
    st.session_state["flashcard_day"] = int(day)

    start_id, end_id = day_word_range(int(day))
    words = models.get_words_range(conn, start_id, end_id)
    if not words:
        st.error("No words found. Make sure the Excel file loaded correctly.")
        return

    st.caption(f"Day {day}: words {start_id}–{end_id}")

    if "flashcard_index" not in st.session_state or st.button("Reset session"):
        st.session_state["flashcard_index"] = 0
        st.session_state["flashcard_flipped"] = False

    idx = int(st.session_state.get("flashcard_index", 0))
    idx = max(0, min(idx, len(words) - 1))
    st.session_state["flashcard_index"] = idx

    w = words[idx]
    word_id = int(w["id"])
    char = str(w["character"])
    pinyin = numbers_to_tone_marks(str(w["pinyin"] or ""))
    meaning = str(w["meaning"] or "")

    st.subheader(f"Card {idx + 1} / {len(words)}")

    flipped = bool(st.session_state.get("flashcard_flipped", False))
    pos = str(w["pos"] or "")
    ex = get_or_create_example(conn, word_id=word_id, word=char, pinyin=pinyin, meaning=meaning, pos=pos)

    char_audio_uri = safe_mp3_data_uri(tts_to_mp3_path(char, lang="zh-CN")) if flipped else None
    ex_audio_uri = safe_mp3_data_uri(tts_to_mp3_path(ex.chinese, lang="zh-CN")) if flipped else None

    image_uri = None
    if flipped:
        img_path = get_or_create_word_image(word_id=word_id, character=char, meaning=meaning)
        image_uri = safe_png_data_uri(img_path) if img_path else None
        if image_uri is None:
            image_uri = fallback_image_data_uri(meaning, char)

    breakdown: list[dict] = []
    if flipped and len(char) > 1:
        for ch in list(char):
            row = models.get_word_by_character(conn, ch)
            if row:
                breakdown.append(
                    {
                        "character": str(row["character"]),
                        "pinyin": numbers_to_tone_marks(str(row["pinyin"] or "")),
                        "meaning": str(row["meaning"] or ""),
                    }
                )

    render_flashcard_card(
        flipped=flipped,
        character=char,
        pinyin=pinyin,
        meaning=meaning,
        example_cn=ex.chinese,
        example_py=numbers_to_tone_marks(ex.pinyin),
        example_en=ex.english,
        word_audio_uri=char_audio_uri,
        example_audio_uri=ex_audio_uri,
        image_uri=image_uri,
        character_breakdown=breakdown,
        height=440,
    )

    pad_l, mid, pad_r = st.columns([1, 6, 1])
    with mid:
        b1, b2, b3 = st.columns([1, 1, 1])
        with b1:
            if st.button("Flip", type="secondary", use_container_width=True):
                st.session_state["flashcard_flipped"] = not flipped
                st.rerun()
        with b2:
            if st.button("I knew this", type="primary", use_container_width=True):
                models.record_flashcard_result(conn, user.id, word_id, knew=True)
                _advance_flashcard(len(words))
        with b3:
            if st.button("I didn't know", use_container_width=True):
                models.record_flashcard_result(conn, user.id, word_id, knew=False)
                _advance_flashcard(len(words))


def _advance_flashcard(total: int) -> None:
    st.session_state["flashcard_flipped"] = False
    st.session_state["flashcard_index"] = min(total - 1, int(st.session_state.get("flashcard_index", 0)) + 1)
    st.rerun()

