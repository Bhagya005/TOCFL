from __future__ import annotations

import streamlit as st

from ai.sentence_generator import get_or_create_example
from audio.embed import safe_mp3_data_uri
from audio.tts import tts_to_mp3_path
from database import models
from flashcards.flashcard_engine import StudyPlan, day_word_range
from ui.components.flashcard_card import render_flashcard_card
from utils.review_queue import get_due_words as rq_get_due_words
from utils.review_queue import get_new_words as rq_get_new_words
from utils.review_queue import get_weak_words as rq_get_weak_words
from utils.spaced_repetition import update_word_progress
from utils.pinyin import numbers_to_tone_marks


def render_flashcards(conn, user: models.User, plan: StudyPlan) -> None:
    st.title("Today's Flashcards")

    # Global counters
    total_weak = len(rq_get_weak_words(conn, user.id, limit=300))
    total_due = len(rq_get_due_words(conn, limit=300))
    total_new = len(rq_get_new_words(conn, limit=300))

    st.markdown(
        f"📚 Words due today: **{total_due}**  \n"
        f"🆕 New words: **{total_new}**  \n"
        f"⚠ Weak words: **{total_weak}**"
    )

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
    # Build session queue: weak -> due -> new, within the day's range.
    weak_words = rq_get_weak_words(conn, user.id, limit=300, start_id=start_id, end_id=end_id)
    due_words = rq_get_due_words(conn, limit=300, start_id=start_id, end_id=end_id)
    new_words = rq_get_new_words(conn, limit=300, start_id=start_id, end_id=end_id)

    session_order: dict[int, object] = {}
    for group in (weak_words, due_words, new_words):
        for row in group:
            wid = int(row["id"])
            if wid not in session_order:
                session_order[wid] = row

    words = list(session_order.values())
    if not words:
        st.info("No flashcards are due for review in this range.")
        return

    st.caption(f"Day {day}: words {start_id}–{end_id}")

    if "flashcard_index" not in st.session_state or st.button("Reset session"):
        st.session_state["flashcard_index"] = 0
        st.session_state["flashcard_flipped"] = False
        st.session_state["flashcards_completed_once"] = False

    idx = int(st.session_state.get("flashcard_index", 0))
    idx = max(0, min(idx, len(words) - 1))
    st.session_state["flashcard_index"] = idx

    w = words[idx]
    word_id = int(w["id"])
    char = str(w["character"])
    pinyin = numbers_to_tone_marks(str(w["pinyin"] or ""))
    meaning = str(w["meaning"] or "")

    st.subheader(f"Card {idx + 1} / {len(words)}")

    mastery = models.get_word_mastery(conn, user.id, word_id)
    reading_mark = "✓" if mastery["reading_correct"] else "✗"
    listening_mark = "✓" if mastery["listening_correct"] else "✗"
    writing_mark = "✓" if mastery["writing_correct"] else "✗"
    status = "Mastered" if mastery["mastered"] else "Learning"

    st.caption(
        f"Reading {reading_mark} · Listening {listening_mark} · Writing {writing_mark}  \n"
        f"Status: {status}"
    )

    flipped = bool(st.session_state.get("flashcard_flipped", False))
    pos = str(w["pos"] or "")
    ex = get_or_create_example(conn, word_id=word_id, word=char, pinyin=pinyin, meaning=meaning, pos=pos)

    char_audio_uri = safe_mp3_data_uri(tts_to_mp3_path(char, lang="zh-CN")) if flipped else None
    example_audio_uri = safe_mp3_data_uri(tts_to_mp3_path(ex.chinese, lang="zh-CN")) if flipped else None

    render_flashcard_card(
        flipped=flipped,
        character=char,
        pinyin=pinyin,
        meaning=meaning,
        example_cn=ex.chinese,
        example_py=ex.pinyin,
        example_en=ex.english,
        word_audio_uri=char_audio_uri,
        example_audio_uri=example_audio_uri,
        height=440,
    )

    pad_l, mid, pad_r = st.columns([1, 6, 1])
    with mid:
        b1, b2, b3 = st.columns([1, 1, 1])
        with b1:
            if st.button("Flip", type="secondary", width="stretch"):
                st.session_state["flashcard_flipped"] = not flipped
                st.rerun()
        with b2:
            if st.button("I knew this", type="primary", width="stretch"):
                update_word_progress(conn, word_id, knew=True)
                models.record_flashcard_result(conn, user.id, word_id, knew=True)
                _advance_flashcard(len(words))
        with b3:
            if st.button("I didn't know", width="stretch"):
                update_word_progress(conn, word_id, knew=False)
                models.record_flashcard_result(conn, user.id, word_id, knew=False)
                _advance_flashcard(len(words))

    if st.session_state.get("flashcards_completed_once") or idx == len(words) - 1:
        if st.button("Review Today's Words Again"):
            st.session_state["flashcard_index"] = 0
            st.session_state["flashcard_flipped"] = False
            st.session_state["flashcards_completed_once"] = False
            st.rerun()


def _advance_flashcard(total: int) -> None:
    cur = int(st.session_state.get("flashcard_index", 0))
    if cur >= total - 1:
        st.session_state["flashcards_completed_once"] = True
        st.session_state["flashcard_index"] = total - 1
    else:
        st.session_state["flashcard_index"] = cur + 1
    st.session_state["flashcard_flipped"] = False
    st.rerun()

