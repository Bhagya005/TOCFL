from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Any, Literal

from openai import OpenAI


QuestionType = Literal[
    "char_to_meaning",
    "meaning_to_char",
    "pinyin_to_char",
    "sentence_to_meaning",
]

SectionType = Literal["meaning", "listening", "writing"]


@dataclass(frozen=True)
class MCQ:
    qtype: QuestionType
    prompt: str
    options: list[str]
    answer_index: int
    word_id: int


def build_three_section_test(
    words: list[dict[str, Any]],
    n_meaning: int,
    n_listening: int,
    n_writing: int,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Build a test with 3 sections: Meaning/Reading, Listening, Writing (Pinyin).
    Returns a list of question dicts, each with 'section' and section-specific fields.
    """
    rng = random.Random(seed)
    pool = [w for w in words if w.get("character")]
    if len(pool) < 4:
        raise ValueError("Not enough words to generate a test.")

    questions: list[dict[str, Any]] = []

    # 1. Meaning / Reading: Chinese → English, Pinyin → English, Sentence → English
    meaning_qs = _generate_meaning_section(pool, min(n_meaning, len(pool) * 2), rng)
    questions.extend(meaning_qs[:n_meaning])

    # 2. Listening: play audio (word or sentence), 4 Chinese options
    listening_qs = _generate_listening_section(pool, min(n_listening, len(pool)), rng)
    questions.extend(listening_qs[:n_listening])

    # 3. Writing: show English meaning, user types pinyin (match 漢拼 → 正體字)
    writing_qs = _generate_writing_section(pool, min(n_writing, len(pool)), rng)
    questions.extend(writing_qs[:n_writing])

    rng.shuffle(questions)
    return questions


def _generate_meaning_section(
    pool: list[dict[str, Any]],
    n: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Meaning/Reading: Chinese → English, Pinyin → English, or Sentence → English."""
    qtypes: list[Literal["char_to_meaning", "pinyin_to_meaning", "sentence_to_meaning"]] = [
        "char_to_meaning",
        "pinyin_to_meaning",
        "sentence_to_meaning",
        "sentence_to_meaning",
    ]
    selected = rng.sample(pool, k=min(n, len(pool)))
    out: list[dict[str, Any]] = []
    for w in selected:
        qtype = rng.choice(qtypes)
        q = _build_meaning_question(w, pool, qtype, rng)
        if q:
            out.append(q)
        if len(out) >= n:
            break
    return out


def _build_meaning_question(
    w: dict[str, Any],
    pool: list[dict[str, Any]],
    qtype: str,
    rng: random.Random,
) -> dict[str, Any] | None:
    wid = int(w["id"])
    char = str(w.get("character", "")).strip()
    pinyin = str(w.get("pinyin", "") or "").strip()
    meaning = str(w.get("meaning", "") or "").strip()
    sentence = str(w.get("example_sentence", "") or "").strip()
    translation = str(w.get("example_translation", "") or "").strip()

    if qtype == "char_to_meaning":
        prompt = f"{char} means?"
        correct = meaning or "(meaning missing)"
        distractors = _sample_unique(
            [str(x.get("meaning", "") or "").strip() for x in pool],
            exclude={correct, ""},
            k=3,
            rng=rng,
            fallback_prefix="Meaning",
        )
    elif qtype == "pinyin_to_meaning":
        prompt = f"{pinyin or char} means?"
        correct = meaning or "(meaning missing)"
        distractors = _sample_unique(
            [str(x.get("meaning", "") or "").strip() for x in pool],
            exclude={correct, ""},
            k=3,
            rng=rng,
            fallback_prefix="Meaning",
        )
    else:
        # sentence_to_meaning
        if not sentence or not translation:
            prompt = f"{char} means?"
            correct = meaning or "(meaning missing)"
            distractors = _sample_unique(
                [str(x.get("meaning", "") or "").strip() for x in pool],
                exclude={correct, ""},
                k=3,
                rng=rng,
                fallback_prefix="Meaning",
            )
        else:
            prompt = f"What does this sentence mean?\n\n{sentence}"
            correct = translation
            distractors = _sample_unique(
                [str(x.get("example_translation", "") or "").strip() for x in pool],
                exclude={correct, ""},
                k=3,
                rng=rng,
                fallback_prefix="Meaning",
            )

    options = distractors + [correct]
    rng.shuffle(options)
    answer_index = options.index(correct)
    return {
        "section": "meaning",
        "prompt": prompt,
        "options": options,
        "answer_index": answer_index,
        "word_id": wid,
    }


def _generate_listening_section(
    pool: list[dict[str, Any]],
    n: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Listening: text_to_play (word or example), 4 Chinese options."""
    selected = rng.sample(pool, k=min(n, len(pool)))
    out: list[dict[str, Any]] = []
    for w in selected:
        q = _build_listening_question(w, pool, rng)
        if q:
            out.append(q)
        if len(out) >= n:
            break
    return out


def _build_listening_question(
    w: dict[str, Any],
    pool: list[dict[str, Any]],
    rng: random.Random,
) -> dict[str, Any] | None:
    wid = int(w["id"])
    char = str(w.get("character", "")).strip()
    pinyin_raw = str(w.get("pinyin", "") or "").strip()
    sentence = str(w.get("example_sentence", "") or "").strip()
    sentence_pinyin_raw = str(w.get("example_pinyin", "") or "").strip()

    text_to_play = sentence if sentence else char

    # For review: display the exact Chinese text plus its pinyin (as stored).
    if sentence:
        display_cn = sentence
        display_py = sentence_pinyin_raw
    else:
        display_cn = char
        display_py = pinyin_raw
    correct = char
    distractors = _sample_unique(
        [str(x.get("character", "")).strip() for x in pool],
        exclude={correct, ""},
        k=3,
        rng=rng,
        fallback_prefix="字",
    )
    options = distractors + [correct]
    rng.shuffle(options)
    answer_index = options.index(correct)
    return {
        "section": "listening",
        "text_to_play": text_to_play,
        "display_cn": display_cn,
        "display_py": display_py,
        "options": options,
        "answer_index": answer_index,
        "word_id": wid,
    }


def _generate_writing_section(
    pool: list[dict[str, Any]],
    n: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Writing: show English meaning, user types pinyin (tone marks). Match 漢拼 → 正體字."""
    selected = rng.sample(pool, k=min(n, len(pool)))
    out: list[dict[str, Any]] = []
    for w in selected:
        q = _build_writing_question(w)
        if q:
            out.append(q)
        if len(out) >= n:
            break
    return out


def _build_writing_question(w: dict[str, Any]) -> dict[str, Any] | None:
    wid = int(w["id"])
    meaning = str(w.get("meaning", "") or "").strip()
    char = str(w.get("character", "")).strip()
    pinyin_raw = str(w.get("pinyin", "") or "").strip()
    if not meaning or not char:
        return None
    # Use the exact pinyin from the database as-is (no conversion).
    return {
        "section": "writing",
        "prompt": meaning,
        "correct_pinyin": pinyin_raw,
        "correct_character": char,
        "word_id": wid,
    }


def _get_client() -> OpenAI | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    return OpenAI(api_key=key)


def generate_mcq_test(
    words: list[dict[str, Any]],
    n_questions: int,
    seed: int | None = None,
) -> list[MCQ]:
    """
    words: list of dicts with keys: id, character, pinyin, meaning
    """
    rng = random.Random(seed)
    pool = [w for w in words if w.get("character")]
    if len(pool) < 8:
        raise ValueError("Not enough words to generate a test.")

    selected = rng.sample(pool, k=min(n_questions, len(pool)))
    # Weighting: include more sentence questions when sentence fields are present.
    qtypes: list[QuestionType] = [
        "char_to_meaning",
        "meaning_to_char",
        "pinyin_to_char",
        "sentence_to_meaning",
        "sentence_to_meaning",
    ]
    questions: list[MCQ] = []

    # First: offline distractors.
    for w in selected:
        qtype = rng.choice(qtypes)
        questions.append(_build_question_offline(w, pool, qtype, rng))

    # Second: optionally refine distractors using OpenAI in one batch.
    client = _get_client()
    if client is not None:
        questions = _maybe_refine_with_openai(client, questions)

    return questions


def _build_question_offline(
    w: dict[str, Any],
    pool: list[dict[str, Any]],
    qtype: QuestionType,
    rng: random.Random,
) -> MCQ:
    wid = int(w["id"])
    char = str(w.get("character", "")).strip()
    pinyin = str(w.get("pinyin", "") or "").strip()
    meaning = str(w.get("meaning", "") or "").strip()
    sentence = str(w.get("example_sentence", "") or "").strip()
    translation = str(w.get("example_translation", "") or "").strip()

    if qtype == "char_to_meaning":
        prompt = f"{char} means?"
        correct = meaning or "(meaning missing)"
        distractors = _sample_unique(
            [str(x.get("meaning", "") or "").strip() for x in pool],
            exclude={correct, ""},
            k=3,
            rng=rng,
            fallback_prefix="Meaning",
        )
    elif qtype == "meaning_to_char":
        prompt = f"“{meaning or char}” → ?"
        correct = char
        distractors = _sample_unique(
            [str(x.get("character", "")).strip() for x in pool],
            exclude={correct, ""},
            k=3,
            rng=rng,
            fallback_prefix="字",
        )
    elif qtype == "pinyin_to_char":
        prompt = f"{pinyin or char} → ?"
        correct = char
        distractors = _sample_unique(
            [str(x.get("character", "")).strip() for x in pool],
            exclude={correct, ""},
            k=3,
            rng=rng,
            fallback_prefix="字",
        )
    else:
        # sentence_to_meaning
        if not sentence or not translation:
            # Fallback to char_to_meaning if sentence data is missing.
            prompt = f"{char} means?"
            correct = meaning or "(meaning missing)"
            distractors = _sample_unique(
                [str(x.get("meaning", "") or "").strip() for x in pool],
                exclude={correct, ""},
                k=3,
                rng=rng,
                fallback_prefix="Meaning",
            )
        else:
            prompt = f"What does this sentence mean?\n\n{sentence}"
            correct = translation
            distractors = _sample_unique(
                [str(x.get("example_translation", "") or "").strip() for x in pool],
                exclude={correct, ""},
                k=3,
                rng=rng,
                fallback_prefix="Meaning",
            )

    options = distractors + [correct]
    rng.shuffle(options)
    answer_index = options.index(correct)
    return MCQ(qtype=qtype, prompt=prompt, options=options, answer_index=answer_index, word_id=wid)


def _sample_unique(
    items: list[str],
    exclude: set[str],
    k: int,
    rng: random.Random,
    fallback_prefix: str,
) -> list[str]:
    uniq = []
    seen = set(exclude)
    candidates = [x for x in items if x and x not in seen]
    rng.shuffle(candidates)
    for x in candidates:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
        if len(uniq) >= k:
            return uniq
    while len(uniq) < k:
        val = f"{fallback_prefix} {len(uniq) + 1}"
        if val not in seen:
            uniq.append(val)
            seen.add(val)
    return uniq


def _maybe_refine_with_openai(client: OpenAI, questions: list[MCQ]) -> list[MCQ]:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    payload = [
        {
            "qtype": q.qtype,
            "prompt": q.prompt,
            "correct": q.options[q.answer_index],
        }
        for q in questions
    ]
    prompt = """You are helping create multiple-choice distractor options for TOCFL A1 learners.
For each item, produce exactly 3 plausible distractors that are NOT the correct answer.
Return STRICT JSON:
{ "items": [ { "distractors": ["...","...","..."] } , ... ] }
The output array length must match the input array length.
"""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Output must be strict JSON."},
                {"role": "user", "content": prompt + "\nINPUT:\n" + json.dumps(payload, ensure_ascii=False)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = _safe_json(resp.choices[0].message.content or "{}")
        items = data.get("items", [])
        if not isinstance(items, list) or len(items) != len(questions):
            return questions
        refined: list[MCQ] = []
        for q, it in zip(questions, items):
            ds = it.get("distractors")
            if not isinstance(ds, list) or len(ds) != 3:
                refined.append(q)
                continue
            correct = q.options[q.answer_index]
            distractors = [str(x).strip() for x in ds if str(x).strip() and str(x).strip() != correct]
            if len(distractors) < 3:
                refined.append(q)
                continue
            options = distractors[:3] + [correct]
            random.shuffle(options)
            refined.append(
                MCQ(
                    qtype=q.qtype,
                    prompt=q.prompt,
                    options=options,
                    answer_index=options.index(correct),
                    word_id=q.word_id,
                )
            )
        return refined
    except Exception:
        return questions


def _safe_json(s: str) -> dict:
    try:
        return json.loads(s)
    except Exception:
        return {}

