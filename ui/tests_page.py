from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Callable

import streamlit as st

from ai.test_generator import MCQ
from database import models


def render_test_page(
    conn,
    user: models.User,
    title: str,
    test_type: str,
    build_questions: Callable[[list[dict], int | None], list[MCQ]],
    eligible_words: list[dict],
    seed: int | None = None,
) -> None:
    st.title(title)

    today = date.today()
    cache_key = f"test_state::{test_type}"

    cstart, cregen = st.columns([1, 1])
    with cstart:
        start_clicked = st.button("Start / Resume test", type="primary")
    with cregen:
        regen_clicked = st.button("Regenerate (discard cached)", type="secondary")

    if regen_clicked:
        models.delete_cached_generated_test(conn, user.id, today, test_type)
        st.session_state.pop(cache_key, None)
        st.success("Discarded cached test. Click Start to generate a new one.")
        st.rerun()

    if start_clicked:
        _ensure_test_loaded(conn, user, today, test_type, build_questions, eligible_words, seed)
        st.session_state[cache_key]["started"] = True
        st.rerun()

    state = st.session_state.get(cache_key)
    if not state or not state.get("started"):
        st.info("Click **Start / Resume test** to begin.")
        latest = models.get_latest_test_result(conn, user.id, test_type, today)
        if latest:
            st.success(f"Already completed today: {latest['score']} / {latest['total']}")
        return

    questions: list[dict] = state["questions"]
    idx = int(state.get("idx", 0))
    answers: dict[int, int] = state.get("answers", {})

    if idx >= len(questions):
        _render_test_finish(conn, user, today, test_type, questions, answers, cache_key)
        return

    q = questions[idx]
    st.subheader(f"Question {idx + 1} / {len(questions)}")
    prompt = str(q["prompt"])
    if "\n" in prompt:
        st.markdown(prompt.replace("\n", "<br>"), unsafe_allow_html=True)
    else:
        st.write(prompt)

    choice = st.radio(
        "Choose one",
        options=list(range(len(q["options"]))),
        format_func=lambda i: q["options"][i],
        index=answers.get(idx, 0),
        key=f"{cache_key}::q::{idx}",
    )

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("Previous", disabled=(idx == 0)):
            answers[idx] = int(choice)
            state["answers"] = answers
            state["idx"] = idx - 1
            st.session_state[cache_key] = state
            st.rerun()
    with c2:
        if st.button("Next", type="primary"):
            answers[idx] = int(choice)
            state["answers"] = answers
            state["idx"] = idx + 1
            st.session_state[cache_key] = state
            st.rerun()
    with c3:
        st.caption("Your answers are saved locally in this session until you finish.")


def _ensure_test_loaded(
    conn,
    user: models.User,
    day: date,
    test_type: str,
    build_questions: Callable[[list[dict], int | None], list[MCQ]],
    eligible_words: list[dict],
    seed: int | None,
) -> None:
    cache_key = f"test_state::{test_type}"
    if cache_key in st.session_state and st.session_state[cache_key].get("questions"):
        return

    cached = models.get_cached_generated_test(conn, user.id, day, test_type)
    if cached and cached.get("questions"):
        questions = cached["questions"]
    else:
        mcqs = build_questions(eligible_words, seed)
        questions = [_mcq_to_dict(q) for q in mcqs]
        models.save_cached_generated_test(conn, user.id, day, test_type, {"questions": questions})

    st.session_state[cache_key] = {"questions": questions, "idx": 0, "answers": {}, "started": False}


def _render_test_finish(conn, user: models.User, day: date, test_type: str, questions: list[dict], answers: dict[int, int], cache_key: str) -> None:
    total = len(questions)
    score = 0
    for i, q in enumerate(questions):
        if int(answers.get(i, -1)) == int(q["answer_index"]):
            score += 1

    st.subheader("Result")
    st.success(f"Score: {score} / {total}")

    already = models.get_latest_test_result(conn, user.id, test_type, day)
    if already:
        st.info("A test result for today already exists. This attempt won’t be stored again.")
    else:
        models.save_test_result(conn, user.id, day, test_type, score=score, total=total, meta={"version": 1})
        st.success("Saved to your progress.")

    if st.button("Finish"):
        st.session_state.pop(cache_key, None)
        st.rerun()


def _mcq_to_dict(q: MCQ) -> dict:
    d = asdict(q)
    # Keep payload stable for caching.
    return {
        "qtype": d["qtype"],
        "prompt": d["prompt"],
        "options": d["options"],
        "answer_index": int(d["answer_index"]),
        "word_id": int(d["word_id"]),
    }

