from __future__ import annotations

import hashlib
from pathlib import Path

from gtts import gTTS


def _cache_dir() -> Path:
    d = Path("cache") / "audio"
    d.mkdir(parents=True, exist_ok=True)
    return d


def tts_to_mp3_path(text: str, lang: str = "zh-CN", slow: bool = False) -> Path | None:
    """
    Returns a cached mp3 file path, or None if generation fails.
    Note: gTTS requires internet access.
    """
    text = (text or "").strip()
    if not text:
        return None

    key = hashlib.sha1(f"{lang}|{int(slow)}|{text}".encode("utf-8")).hexdigest()
    out = _cache_dir() / f"{key}.mp3"
    if out.exists() and out.stat().st_size > 0:
        return out

    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.save(str(out))
        return out if out.exists() and out.stat().st_size > 0 else None
    except Exception:
        if out.exists():
            try:
                out.unlink()
            except Exception:
                pass
        return None

