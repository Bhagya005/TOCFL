from __future__ import annotations

import random

import streamlit as st

from audio.tts import tts_to_mp3_path
from database import models
from flashcards.flashcard_engine import StudyPlan


def _init_quiz_state(total_questions: int) -> None:
    st.session_state.setdefault("listening_quiz_ids", [])
    st.session_state.setdefault("listening_quiz_idx", 0)
    st.session_state.setdefault("listening_quiz_score", 0)
    st.session_state.setdefault("listening_quiz_feedback", None)
    st.session_state.setdefault("listening_quiz_total", total_questions)


def _reset_quiz(words: list[dict], total_questions: int) -> None:
    ids = [int(w["id"]) for w in words]
    random.shuffle(ids)
    st.session_state["listening_quiz_ids"] = ids[:total_questions]
    st.session_state["listening_quiz_idx"] = 0
    st.session_state["listening_quiz_score"] = 0
    st.session_state["listening_quiz_feedback"] = None
    st.session_state["listening_quiz_total"] = total_questions


def render_listening_quiz(conn, user: models.User, plan: StudyPlan) -> None:
    st.title("Listening Quiz")

    # Use unlocked vocabulary for quiz pool.
    words = models.get_words_upto(conn, plan.unlocked_upto_word_id)
    if not words:
        st.info("No vocabulary available yet.")
        return

    # Normalise to simple dicts for easier handling.
    pool = [
        {
            "id": int(w["id"]),
            "character": str(w["character"]),
            "pinyin": str(w["pinyin"] or ""),
            "meaning": str(w["meaning"] or ""),
        }
        for w in words
    ]

    total_questions = min(10, len(pool))
    _init_quiz_state(total_questions)

    if st.button("Restart quiz"):
        _reset_quiz(pool, total_questions)
        st.rerun()

    if not st.session_state["listening_quiz_ids"]:
        _reset_quiz(pool, total_questions)

    ids = st.session_state["listening_quiz_ids"]
    idx = int(st.session_state.get("listening_quiz_idx", 0))
    total = int(st.session_state.get("listening_quiz_total", total_questions))

    if idx >= len(ids):
        score = int(st.session_state.get("listening_quiz_score", 0))
        accuracy = (score / max(1, total)) * 100.0
        st.subheader(f"Score: {score} / {total}")
        st.write(f"Accuracy: {accuracy:.0f}%")
        return

    # Current question
    current_id = ids[idx]
    by_id = {int(w["id"]): w for w in pool}
    current = by_id[current_id]

    st.caption(f"Question {idx + 1} / {total}")

    # Audio only (character hidden initially)
    audio_path = tts_to_mp3_path(current["character"], lang="zh-CN")
    if audio_path is not None:
        audio_bytes = audio_path.read_bytes()
        st.audio(audio_bytes, format="audio/mp3")
    else:
        st.warning("Audio unavailable for this word.")

    # Build options: 1 correct + 3 distractors
    others = [w for w in pool if int(w["id"]) != current_id]
    distractors = random.sample(others, k=min(3, len(others)))
    options = [current] + distractors
    random.shuffle(options)

    letters = ["A", "B", "C", "D"]
    option_labels = [
        f"{letters[i]}) {opt['character']}" for i, opt in enumerate(options)
    ]

    st.write("Choose the correct word:")
    with st.form(f"listening_quiz_form_{idx}"):
        choice_idx = st.radio(
            " ",
            options=list(range(len(options))),
            format_func=lambda i: option_labels[i],
            horizontal=False,
        )
        submitted = st.form_submit_button("Submit answer")

    if submitted:
        correct_idx = next(
            (i for i, opt in enumerate(options) if int(opt["id"]) == current_id),
            None,
        )
        is_correct = choice_idx == correct_idx

        if is_correct:
            st.session_state["listening_quiz_score"] = int(
                st.session_state.get("listening_quiz_score", 0)
            ) + 1
            st.success("Correct!")
        else:
            st.error(
                f"Incorrect. The correct answer was {current['character']} "
                f"({current['pinyin']}) – {current['meaning']}."
            )

        # Move to next question after feedback.
        st.session_state["listening_quiz_idx"] = idx + 1
        st.rerun()

