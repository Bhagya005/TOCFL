from __future__ import annotations

import hashlib
import os
from pathlib import Path

from openai import OpenAI


def _get_client() -> OpenAI | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    return OpenAI(api_key=key)


def _cache_dir() -> Path:
    d = Path("cache") / "images"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_or_create_word_image(
    word_id: int,
    character: str,
    meaning: str | None,
) -> Path | None:
    """
    Creates a small icon-like image for the word, cached locally.
    Returns path to PNG or None.
    """
    char = (character or "").strip()
    if not char:
        return None

    m = (meaning or "").strip()
    key = hashlib.sha1(f"{word_id}|{char}|{m}".encode("utf-8")).hexdigest()
    out = _cache_dir() / f"{key}.png"
    if out.exists() and out.stat().st_size > 0:
        return out

    client = _get_client()
    if client is None:
        return None

    # Keep cost down: small, simple, consistent style.
    prompt = f"""
Create a simple, clean, flat illustration (icon style) for a beginner Chinese vocabulary flashcard.
No text, no letters, no numbers, no watermarks.
Meaning: {m or char}
Style: minimal, friendly, high-contrast, centered subject, plain background.
"""
    model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1").strip() or "gpt-image-1"
    try:
        resp = client.images.generate(
            model=model,
            prompt=prompt.strip(),
            size="256x256",
        )
        b64 = resp.data[0].b64_json
        if not b64:
            return None
        import base64

        out.write_bytes(base64.b64decode(b64))
        return out if out.exists() and out.stat().st_size > 0 else None
    except Exception:
        if out.exists():
            try:
                out.unlink()
            except Exception:
                pass
        return None

