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


@dataclass(frozen=True)
class MCQ:
    qtype: QuestionType
    prompt: str
    options: list[str]
    answer_index: int
    word_id: int


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

