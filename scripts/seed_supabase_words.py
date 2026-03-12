#!/usr/bin/env python3
"""
Seed the Supabase `words` table (and optionally `examples`) from CCCC_Vocabulary_2022.xlsx.
Run from project root. Requires the Excel file in the project root.

  export NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
  export SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
  python scripts/seed_supabase_words.py

Or copy frontend/.env.local to a .env in project root and load with python-dotenv.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Project root = parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(PROJECT_ROOT / "frontend" / ".env.local")
except ImportError:
    pass

from data.vocab_loader import load_vocab_first_300


def main() -> None:
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        print("Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY)")
        sys.exit(1)

    excel_path = PROJECT_ROOT / "CCCC_Vocabulary_2022.xlsx"
    if not excel_path.exists():
        print(f"Excel not found: {excel_path}")
        sys.exit(1)

    vocab = load_vocab_first_300(excel_path)
    words_payload = [
        {
            "id": v.id,
            "character": v.character,
            "pinyin": v.pinyin or None,
            "meaning": v.meaning or None,
            "pos": v.pos or None,
            "category": v.category or None,
            "subcategory": v.subcategory or None,
        }
        for v in vocab
    ]

    import urllib.request
    import urllib.error

    base = url.rstrip("/")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    # Upsert words in batches of 100
    batch_size = 100
    for i in range(0, len(words_payload), batch_size):
        batch = words_payload[i : i + batch_size]
        req = urllib.request.Request(
            f"{base}/rest/v1/words",
            data=json.dumps(batch).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                pass
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"Supabase error ({e.code}): {body}")
            sys.exit(1)
        print(f"Upserted words {i + 1}-{i + len(batch)}")

    # Optional: seed examples from Excel (sentence, pinyin, translation)
    examples_payload = []
    for v in vocab:
        if v.example and (v.example_pinyin or v.example_meaning):
            examples_payload.append({
                "word_id": v.id,
                "sentence": v.example.strip(),
                "pinyin": (v.example_pinyin or "").strip() or v.example.strip(),
                "translation": (v.example_meaning or "").strip() or "(no translation)",
            })

    if examples_payload:
        for i in range(0, len(examples_payload), batch_size):
            batch = examples_payload[i : i + batch_size]
            req = urllib.request.Request(
                f"{base}/rest/v1/examples",
                data=json.dumps(batch).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            req.add_header("Prefer", "resolution=merge-duplicates")
            try:
                with urllib.request.urlopen(req) as resp:
                    pass
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                print(f"Examples Supabase error ({e.code}): {body}")
            else:
                print(f"Upserted examples for words {batch[0]['word_id']}-{batch[-1]['word_id']}")

    print(f"Done. {len(words_payload)} words in Supabase.")


if __name__ == "__main__":
    main()
