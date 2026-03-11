from __future__ import annotations

from datetime import date
from typing import Any, Callable
import csv
import io

import streamlit as st

from audio.tts import tts_to_mp3_path
from database import models


def render_test_page(
    conn,
    user: models.User,
    title: str,
    test_type: str,
    build_questions: Callable[[list[dict], int | None], list[dict]],
    eligible_words: list[dict],
    seed: int | None = None,
) -> None:
    st.title(title)

    today = date.today()
    cache_key = f"test_state::{test_type}::user::{user.id}"

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
            total = int(latest.get("total", 0))
            score = int(latest.get("score", 0))
            pct = (100.0 * score / total) if total else 0
            st.success(f"Already completed today: {score} / {total} ({pct:.0f}%)")
        return

    questions: list[dict] = state["questions"]
    idx = int(state.get("idx", 0))
    answers: dict[int, Any] = state.get("answers", {})

    if idx >= len(questions):
        _render_test_finish(conn, user, today, test_type, questions, answers, cache_key)
        return

    q = questions[idx]
    section = q.get("section", "meaning")
    st.subheader(f"Question {idx + 1} / {len(questions)}")
    if section in ("meaning", "listening"):
        st.caption(_section_label(section))

    if section == "meaning":
        _render_meaning_question(q, idx, answers, cache_key, state)
    elif section == "listening":
        _render_listening_question(q, idx, answers, cache_key, state)
    else:
        _render_writing_question(q, idx, answers, cache_key, state)


def _section_label(section: str) -> str:
    if section == "meaning":
        return "Meaning / Reading"
    if section == "listening":
        return "Listening"
    if section == "writing":
        return "Writing (Pinyin)"
    return ""


def _render_meaning_question(
    q: dict,
    idx: int,
    answers: dict[int, Any],
    cache_key: str,
    state: dict,
) -> None:
    prompt = str(q.get("prompt", ""))
    if "\n" in prompt:
        st.markdown(prompt.replace("\n", "<br>"), unsafe_allow_html=True)
    else:
        st.write(prompt)
    options = q.get("options", [])
    choice = st.radio(
        "Choose one",
        options=list(range(len(options))),
        format_func=lambda i: options[i],
        index=_get_mcq_answer(answers.get(idx), len(options)),
        key=f"{cache_key}::q::{idx}",
    )
    _nav_buttons(idx, int(choice), answers, cache_key, state)


def _render_listening_question(
    q: dict,
    idx: int,
    answers: dict[int, Any],
    cache_key: str,
    state: dict,
) -> None:
    text_to_play = str(q.get("text_to_play", "")).strip()
    if text_to_play:
        audio_path = tts_to_mp3_path(text_to_play, lang="zh-CN")
        if audio_path:
            st.audio(str(audio_path.resolve()), format="audio/mpeg")
        else:
            st.caption("(Audio unavailable)")
    options = q.get("options", [])
    choice = st.radio(
        "Choose the word you heard",
        options=list(range(len(options))),
        format_func=lambda i: options[i],
        index=_get_mcq_answer(answers.get(idx), len(options)),
        key=f"{cache_key}::q::{idx}",
    )
    _nav_buttons(idx, int(choice), answers, cache_key, state)


def _render_writing_question(
    q: dict,
    idx: int,
    answers: dict[int, Any],
    cache_key: str,
    state: dict,
) -> None:
    prompt = str(q.get("prompt", ""))
    st.write("English:", prompt)
    st.caption("Type the pinyin with tone numbers (e.g. peng2you3)")
    existing = answers.get(idx)
    if isinstance(existing, str):
        default = existing
    else:
        default = ""
    user_pinyin = st.text_input(
        "Pinyin",
        value=default,
        key=f"{cache_key}::writing::{idx}",
        label_visibility="collapsed",
    )
    _nav_buttons(idx, user_pinyin, answers, cache_key, state)


def _get_mcq_answer(val: Any, n_options: int) -> int:
    if isinstance(val, int) and 0 <= val < n_options:
        return val
    return 0


def _nav_buttons(
    idx: int,
    choice: Any,
    answers: dict[int, Any],
    cache_key: str,
    state: dict,
) -> None:
    questions = state["questions"]
    answers[idx] = choice
    state["answers"] = answers

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("Previous", disabled=(idx == 0), key=f"{cache_key}::prev::{idx}"):
            state["idx"] = idx - 1
            st.session_state[cache_key] = state
            st.rerun()
    with c2:
        if st.button("Next", type="primary", key=f"{cache_key}::next::{idx}"):
            state["idx"] = idx + 1
            st.session_state[cache_key] = state
            st.rerun()
    with c3:
        st.caption("Your answers are saved locally until you finish.")


def _ensure_test_loaded(
    conn,
    user: models.User,
    day: date,
    test_type: str,
    build_questions: Callable[[list[dict], int | None], list[dict]],
    eligible_words: list[dict],
    seed: int | None,
) -> None:
    cache_key = f"test_state::{test_type}::user::{user.id}"
    if cache_key in st.session_state and st.session_state[cache_key].get("questions"):
        return

    cached = models.get_cached_generated_test(conn, user.id, day, test_type)
    if cached and cached.get("questions"):
        questions = cached["questions"]
    else:
        questions = build_questions(eligible_words, seed)
        models.save_cached_generated_test(conn, user.id, day, test_type, {"questions": questions})

    st.session_state[cache_key] = {"questions": questions, "idx": 0, "answers": {}, "started": False}


def _normalize_pinyin(s: str) -> str:
    """Strip and collapse spaces for comparison."""
    if not s or not isinstance(s, str):
        return ""
    return " ".join(s.strip().split()).lower()


def _render_test_finish(
    conn,
    user: models.User,
    day: date,
    test_type: str,
    questions: list[dict],
    answers: dict[int, Any],
    cache_key: str,
) -> None:
    total = len(questions)
    meaning_correct = 0
    listening_correct = 0
    writing_correct = 0
    meaning_total = 0
    listening_total = 0
    writing_total = 0

    for i, q in enumerate(questions):
        section = q.get("section", "meaning")
        user_ans = answers.get(i)

        if section == "meaning":
            meaning_total += 1
            if isinstance(user_ans, int) and int(user_ans) == int(q.get("answer_index", -1)):
                meaning_correct += 1
        elif section == "listening":
            listening_total += 1
            if isinstance(user_ans, int) and int(user_ans) == int(q.get("answer_index", -1)):
                listening_correct += 1
        else:
            writing_total += 1
            correct_pinyin_numbers = str(q.get("correct_pinyin_numbers", "")).strip()
            if correct_pinyin_numbers and isinstance(user_ans, str):
                user_raw = user_ans.strip().lower().replace(" ", "")
                correct_raw = correct_pinyin_numbers.strip().lower().replace(" ", "")
                if user_raw and correct_raw and user_raw == correct_raw:
                    writing_correct += 1

    total_correct = meaning_correct + listening_correct + writing_correct
    accuracy_percent = (100.0 * total_correct / total) if total else 0.0

    # Build per-question review data
    review_rows: list[dict[str, Any]] = []
    for i, q in enumerate(questions):
        section = q.get("section", "meaning")
        user_ans = answers.get(i)
        if section == "meaning":
            options = q.get("options", [])
            correct_idx = int(q.get("answer_index", -1))
            correct_text = options[correct_idx] if 0 <= correct_idx < len(options) else ""
            if isinstance(user_ans, int) and 0 <= user_ans < len(options):
                user_text = options[user_ans]
            else:
                user_text = "(no answer)"
            is_correct = isinstance(user_ans, int) and int(user_ans) == int(q.get("answer_index", -1))
            question_text = str(q.get("prompt", ""))
        elif section == "listening":
            options = q.get("options", [])
            correct_idx = int(q.get("answer_index", -1))
            correct_text = options[correct_idx] if 0 <= correct_idx < len(options) else ""
            if isinstance(user_ans, int) and 0 <= user_ans < len(options):
                user_text = options[user_ans]
            else:
                user_text = "(no answer)"
            is_correct = isinstance(user_ans, int) and int(user_ans) == int(q.get("answer_index", -1))

            display_cn = str(q.get("display_cn", "")).strip()
            display_py = str(q.get("display_py", "")).strip()
            if display_cn and display_py:
                question_text = f"{display_cn} ({display_py})"
            elif display_cn:
                question_text = display_cn
            else:
                question_text = "(listening question)"
        else:
            correct_pinyin_numbers = str(q.get("correct_pinyin_numbers", "")).strip()
            correct_pinyin_display = str(q.get("correct_pinyin_display", "")).strip()
            user_text = user_ans if isinstance(user_ans, str) and user_ans.strip() else "(no answer)"
            user_raw = user_ans.strip().lower().replace(" ", "") if isinstance(user_ans, str) else ""
            correct_raw = correct_pinyin_numbers.strip().lower().replace(" ", "")
            is_correct = bool(user_raw and correct_raw and user_raw == correct_raw)
            question_text = f"English: {q.get('prompt', '')}"
            # Show display pinyin (tone marks) if available; otherwise fall back to numbered pinyin.
            correct_text = correct_pinyin_display or correct_pinyin_numbers

        review_rows.append(
            {
                "Q#": i + 1,
                "Section": section.capitalize(),
                "Question": question_text,
                "Your answer": user_text,
                "Correct answer": correct_text,
                "Result": "Correct" if is_correct else "Incorrect",
            }
        )

    st.subheader("Result")
    st.success(f"Total: {total_correct} / {total} ({accuracy_percent:.0f}%)")
    st.write(
        f"Meaning / Reading: {meaning_correct} / {meaning_total}  |  "
        f"Listening: {listening_correct} / {listening_total}  |  "
        f"Writing: {writing_correct} / {writing_total}"
    )

    st.subheader("Test Review")
    if review_rows:
        st.dataframe(review_rows, hide_index=True, width="stretch")
    else:
        st.caption("No questions to review.")

    already = models.get_latest_test_result(conn, user.id, test_type, day)
    if already:
        st.info("A test result for today already exists. This attempt won't be stored again.")
    else:
        meta = {
            "version": 2,
            "meaning_score": meaning_correct,
            "listening_score": listening_correct,
            "writing_score": writing_correct,
            "accuracy_percent": round(accuracy_percent, 1),
        }
        models.save_test_result(
            conn,
            user.id,
            day,
            test_type,
            score=total_correct,
            total=total,
            meta=meta,
        )
        st.success("Saved to your progress.")

    # Generate downloadable CSV report
    report_buffer = io.StringIO()
    writer = csv.writer(report_buffer)
    writer.writerow(
        [
            "Test type",
            "Date",
            "Total score",
            "Total questions",
            "Meaning score",
            "Meaning total",
            "Listening score",
            "Listening total",
            "Writing score",
            "Writing total",
            "Accuracy percent",
        ]
    )
    writer.writerow(
        [
            test_type,
            day.isoformat(),
            total_correct,
            total,
            meaning_correct,
            meaning_total,
            listening_correct,
            listening_total,
            writing_correct,
            writing_total,
            f"{accuracy_percent:.1f}",
        ]
    )
    writer.writerow([])
    writer.writerow(["Q#", "Section", "Question", "Your answer", "Correct answer", "Result"])
    for row in review_rows:
        writer.writerow(
            [
                row["Q#"],
                row["Section"],
                row["Question"],
                row["Your answer"],
                row["Correct answer"],
                row["Result"],
            ]
        )
    csv_bytes = report_buffer.getvalue().encode("utf-8-sig")

    st.download_button(
        "Download Test Report (CSV)",
        data=csv_bytes,
        file_name=f"{test_type}_test_{day.isoformat()}.csv",
        mime="text/csv",
    )

    if st.button("Finish"):
        st.session_state.pop(cache_key, None)
        st.rerun()
