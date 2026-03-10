from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import sqlite3

from data.vocab_loader import load_vocab_first_300


@dataclass(frozen=True)
class ExampleSentence:
    chinese: str
    pinyin: str
    english: str


EXCEL_FILE = "CCCC_Vocabulary_2022.xlsx"
_EXAMPLES_BY_ID: dict[int, ExampleSentence] | None = None


def _load_examples_from_excel() -> dict[int, ExampleSentence]:
    """
    Load example sentences directly from the Excel dataset.
    Mapping is by word id (same ordering as vocab loader / DB).
    """
    global _EXAMPLES_BY_ID
    if _EXAMPLES_BY_ID is not None:
        return _EXAMPLES_BY_ID

    rows = load_vocab_first_300(Path(EXCEL_FILE))
    out: dict[int, ExampleSentence] = {}
    for v in rows:
        cn = (v.example or "").strip() if hasattr(v, "example") else ""
        if not cn:
            continue
        py = (v.example_pinyin or "").strip() if hasattr(v, "example_pinyin") else ""
        en = (v.example_meaning or "").strip() if hasattr(v, "example_meaning") else ""
        out[int(v.id)] = ExampleSentence(chinese=cn, pinyin=py, english=en)

    _EXAMPLES_BY_ID = out
    return out


def get_or_create_example(
    conn: sqlite3.Connection,
    word_id: int,
    word: str,
    pinyin: str | None,
    meaning: str | None,
    pos: str | None = None,
) -> ExampleSentence:
    """
    Deterministic example lookup: read from Excel only.
    Does NOT call OpenAI or write to the database.
    """
    examples = _load_examples_from_excel()
    ex = examples.get(int(word_id))
    if ex is not None:
        return ex

    # If the dataset has no example for this word, return an empty shell
    # so the UI can handle missing example fields gracefully.
    return ExampleSentence(
        chinese=str(word or ""),
        pinyin=str(pinyin or ""),
        english=str(meaning or ""),
    )

