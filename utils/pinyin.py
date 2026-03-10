from __future__ import annotations

import re


_TONE_MARKS = {
    "a": ["a", "ā", "á", "ǎ", "à"],
    "e": ["e", "ē", "é", "ě", "è"],
    "i": ["i", "ī", "í", "ǐ", "ì"],
    "o": ["o", "ō", "ó", "ǒ", "ò"],
    "u": ["u", "ū", "ú", "ǔ", "ù"],
    "ü": ["ü", "ǖ", "ǘ", "ǚ", "ǜ"],
}


_VOWELS = set("aeiouü")

_BREVE_TO_CARON = str.maketrans(
    {
        "ă": "ǎ",
        "Ă": "Ǎ",
        "ĕ": "ě",
        "Ĕ": "Ě",
        "ĭ": "ǐ",
        "Ĭ": "Ǐ",
        "ŏ": "ǒ",
        "Ŏ": "Ǒ",
        "ŭ": "ǔ",
        "Ŭ": "Ǔ",
    }
)


def numbers_to_tone_marks(pinyin: str) -> str:
    """
    Convert numbered pinyin (ni3, wo3) to tone marks (nǐ, wǒ).

    Handles:
    - whitespace separated syllables
    - v / u: for ü
    - neutral tone (5 or 0) -> no diacritic
    """
    s = (pinyin or "").strip()
    if not s:
        return s

    # Normalize ü inputs.
    s = s.replace("u:", "ü").replace("U:", "Ü").replace("v", "ü").replace("V", "Ü")

    parts = re.split(r"(\s+)", s)
    out: list[str] = []
    for part in parts:
        if part.isspace():
            out.append(part)
            continue
        out.append(_convert_syllable_token(part))
    return "".join(out).translate(_BREVE_TO_CARON)


def _convert_syllable_token(token: str) -> str:
    # Keep punctuation around syllables.
    m = re.match(r"^([^A-Za-züÜ]*)([A-Za-züÜ]+)([0-5]?)([^A-Za-züÜ]*)$", token)
    if not m:
        return token

    pre, core, tone_s, post = m.groups()
    if not tone_s:
        return token

    tone = int(tone_s)
    if tone in (0, 5):
        return f"{pre}{core}{post}"

    core_l = core.lower()
    core_l = core_l.replace("u:", "ü").replace("v", "ü")

    # Choose which vowel to mark (pinyin rules):
    # - if a or e exists, mark the first of those
    # - else if "ou" exists, mark o
    # - else mark the last vowel
    idx = _vowel_index_to_mark(core_l)
    if idx is None:
        return f"{pre}{core}{post}"

    marked = _apply_tone(core_l, idx, tone)
    # Restore capitalization heuristically (rare in our app).
    if core and core[0].isupper():
        marked = marked[0].upper() + marked[1:]
    return f"{pre}{marked}{post}"


def _vowel_index_to_mark(s: str) -> int | None:
    for v in ("a", "e"):
        i = s.find(v)
        if i != -1:
            return i
    i = s.find("ou")
    if i != -1:
        return i  # mark 'o'
    vowel_positions = [i for i, ch in enumerate(s) if ch in _VOWELS]
    return vowel_positions[-1] if vowel_positions else None


def _apply_tone(s: str, idx: int, tone: int) -> str:
    ch = s[idx]
    if ch not in _TONE_MARKS:
        return s
    rep = _TONE_MARKS[ch][tone]
    return s[:idx] + rep + s[idx + 1 :]

