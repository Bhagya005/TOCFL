from __future__ import annotations

from ai.test_generator import build_three_section_test


# Daily: words learned today. Meaning 20, Listening 10, Writing 10. Total 40.
DAILY_MEANING = 20
DAILY_LISTENING = 10
DAILY_WRITING = 10


def build_daily_test(words: list[dict], seed: int | None = None) -> list[dict]:
    return build_three_section_test(
        words=words,
        n_meaning=DAILY_MEANING,
        n_listening=DAILY_LISTENING,
        n_writing=DAILY_WRITING,
        seed=seed,
    )
