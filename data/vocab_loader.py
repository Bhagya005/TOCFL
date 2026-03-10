from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class VocabRow:
    id: int
    character: str
    pinyin: str | None
    meaning: str | None
    pos: str | None
    category: str | None
    subcategory: str | None
    example: str | None
    example_pinyin: str | None
    example_meaning: str | None


def _norm(s: str) -> str:
    return "".join(ch.lower() for ch in str(s).strip() if ch.isalnum())


def load_vocab_first_300(excel_path: str | Path) -> list[VocabRow]:
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    df = pd.read_excel(excel_path, engine="openpyxl")
    if df.empty:
        raise ValueError("Excel file has no rows.")

    # Some versions of this file store the real headers in the first row,
    # and use generic column names like "Unnamed: 1".
    first_row = df.iloc[0].tolist()
    header_markers = {"分類", "分类", "細目", "细目", "正體字", "正体字", "繁體字", "繁体字", "漢拼", "汉拼", "詞性", "词性", "英文"}
    if any(str(x).strip() in header_markers for x in first_row if not pd.isna(x)):
        new_cols = []
        for fallback, x in zip(df.columns, first_row):
            if pd.isna(x) or not str(x).strip():
                new_cols.append(str(fallback))
            else:
                new_cols.append(str(x).strip())
        df = df.iloc[1:].copy()
        df.columns = new_cols
        df = df.reset_index(drop=True)

    # Robust column mapping (handles minor header variations).
    col_map = {_norm(c): c for c in df.columns}

    def pick(*candidates: str) -> str | None:
        for cand in candidates:
            key = _norm(cand)
            if key in col_map:
                return col_map[key]
        return None

    c_category = pick("Category", "分類", "分类")
    c_subcategory = pick("Subcategory", "Sub category", "Sub-Category", "細目", "细目")
    c_trad = pick(
        "Traditional Chinese",
        "Traditional",
        "TraditionalChinese",
        "Trad",
        "繁體",
        "繁體中文",
        "正體字",
        "正体字",
        "繁體字",
        "繁体字",
    )
    c_pinyin = pick("Pinyin", "拼音", "漢拼", "汉拼")
    c_pos = pick("Part of speech", "Partofspeech", "POS", "詞性", "词性")
    c_meaning = pick("English meaning", "Meaning", "English", "英文", "Englishmeaning")
    c_example = pick("Example")
    c_example_pinyin = pick("Example Pinyin")
    c_example_meaning = pick("Example Meaning")

    if not c_trad:
        raise ValueError(
            "Could not find the Traditional Chinese column. "
            "Expected something like 'Traditional Chinese'."
        )

    out: list[VocabRow] = []
    for _, r in df.iterrows():
        char = r.get(c_trad)
        if pd.isna(char):
            continue
        char_s = str(char).strip()
        if not char_s:
            continue

        out.append(
            VocabRow(
                id=len(out) + 1,
                character=char_s,
                pinyin=None if not c_pinyin or pd.isna(r.get(c_pinyin)) else str(r.get(c_pinyin)).strip(),
                meaning=None if not c_meaning or pd.isna(r.get(c_meaning)) else str(r.get(c_meaning)).strip(),
                pos=None if not c_pos or pd.isna(r.get(c_pos)) else str(r.get(c_pos)).strip(),
                category=None if not c_category or pd.isna(r.get(c_category)) else str(r.get(c_category)).strip(),
                subcategory=None if not c_subcategory or pd.isna(r.get(c_subcategory)) else str(r.get(c_subcategory)).strip(),
                example=None if not c_example or pd.isna(r.get(c_example)) else str(r.get(c_example)).strip(),
                example_pinyin=None if not c_example_pinyin or pd.isna(r.get(c_example_pinyin)) else str(r.get(c_example_pinyin)).strip(),
                example_meaning=None if not c_example_meaning or pd.isna(r.get(c_example_meaning)) else str(r.get(c_example_meaning)).strip(),
            )
        )
        if len(out) >= 300:
            break

    if len(out) < 300:
        raise ValueError(f"Expected at least 300 vocab rows, got {len(out)}.")

    return out

