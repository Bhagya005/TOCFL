from __future__ import annotations

import os
import random
import sqlite3
from dataclasses import dataclass

from openai import OpenAI

from database import models
from utils.pinyin import numbers_to_tone_marks


@dataclass(frozen=True)
class ExampleSentence:
    chinese: str
    pinyin: str
    english: str


def _get_client() -> OpenAI | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    return OpenAI(api_key=key)


def get_or_create_example(
    conn: sqlite3.Connection,
    word_id: int,
    word: str,
    pinyin: str | None,
    meaning: str | None,
    pos: str | None = None,
) -> ExampleSentence:
    cached = models.get_example(conn, word_id)
    if cached and not _looks_like_old_fallback(cached):
        return ExampleSentence(
            chinese=str(cached["sentence"]),
            pinyin=numbers_to_tone_marks(str(cached["pinyin"])),
            english=str(cached["translation"]),
        )

    client = _get_client()
    if client is None:
        cn, py, en = _offline_example(word_id, word, pinyin, meaning, pos)
        models.upsert_example(conn, word_id, cn, py, en)
        return ExampleSentence(chinese=cn, pinyin=py, english=en)

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    prompt = f"""Given this Chinese word:

Word: {word}
Pinyin: {pinyin or ""}
Meaning: {meaning or ""}

Generate 1 short beginner-level Chinese example sentence.
Constraints:
- Use Traditional Chinese only.
- Include the target word exactly as provided.
- Output pinyin with tone marks (diacritics), NOT tone numbers.
Return STRICT JSON with keys:
chinese, pinyin, english
"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You generate beginner Chinese examples. Output must be strict JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        data = _safe_json(content)
        cn = str(data.get("chinese", "")).strip()
        py = numbers_to_tone_marks(str(data.get("pinyin", "")).strip())
        en = str(data.get("english", "")).strip()
        if not (cn and py and en):
            raise ValueError("Missing required fields.")
        if word not in cn:
            raise ValueError("Target word not included in sentence.")
    except Exception:
        cn, py, en = _offline_example(word_id, word, pinyin, meaning, pos)

    models.upsert_example(conn, word_id, cn, py, en)
    return ExampleSentence(chinese=cn, pinyin=py, english=en)


def _looks_like_old_fallback(cached_row: sqlite3.Row) -> bool:
    s = str(cached_row["sentence"] or "").strip()
    py = numbers_to_tone_marks(str(cached_row["pinyin"] or "")).strip()
    en = str(cached_row["translation"] or "").strip()
    if not s:
        return False
    return (
        s.startswith("我學會了")
        and ("wǒ xué huì le" in py or "wo3 xue2 hui4 le5" in py)
        and en.lower().startswith("i learned")
    )


def _offline_example(
    word_id: int,
    word: str,
    pinyin: str | None,
    meaning: str | None,
    pos: str | None,
) -> tuple[str, str, str]:
    """
    Deterministic, varied, beginner-friendly offline examples.
    Uses full-sentence pinyin with tone marks.
    """
    w = (word or "").strip()
    m_raw = (meaning or w).strip()
    m_verb = m_raw[3:].strip() if m_raw.lower().startswith("to ") else m_raw
    wp = numbers_to_tone_marks((pinyin or "").strip())
    p = (pos or "").strip().upper()

    rng = random.Random(int(word_id))

    def ex(cn: str, py_: str, en: str) -> tuple[str, str, str]:
        return (cn, numbers_to_tone_marks(py_), en)

    candidates: list[tuple[str, str, str]] = []

    # Generic noun-ish templates
    candidates.append(ex(f"這是{w}。", f"zhè shì {wp}.", f"This is {m_raw}."))
    candidates.append(ex(f"我看到一個{w}。", f"wǒ kàn dào yí gè {wp}.", f"I see a {m_raw}."))
    candidates.append(ex(f"你喜歡{w}嗎？", f"nǐ xǐ huān {wp} ma?", f"Do you like {m_raw}?"))

    # Verb-ish templates
    candidates.append(ex(f"我會{w}。", f"wǒ huì {wp}.", f"I can {m_verb}."))
    candidates.append(ex(f"我想{w}。", f"wǒ xiǎng {wp}.", f"I want to {m_verb}."))

    # Adjective-ish templates
    candidates.append(ex(f"今天很{w}。", f"jīn tiān hěn {wp}.", f"Today is very {m_raw}."))

    # Light POS-based bias: pick from subsets when POS is known.
    if p.startswith("V"):
        preferred = candidates[3:5] + candidates[0:2]
    elif p.startswith("ADJ") or p.startswith("A"):
        preferred = [candidates[5], candidates[0], candidates[2]]
    else:
        preferred = candidates[0:3] + candidates[3:4]

    # Remove candidates with missing word pinyin (keep usable)
    filtered = [c for c in preferred if w and c[0].find(w) != -1]
    if not wp:
        # If we don't have word pinyin, still return a Chinese+English sentence and omit pinyin.
        cn, _, en = rng.choice(filtered or preferred)
        return (cn, "", en)

    cn, py_out, en = rng.choice(filtered or preferred)
    return (cn, py_out, en)


def _safe_json(s: str) -> dict:
    import json

    try:
        return json.loads(s)
    except Exception:
        return {}

