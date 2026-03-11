from __future__ import annotations

from ai.test_generator import build_three_section_test


# Weekly: 3× daily counts. Meaning 60, Listening 30, Writing 30. Total 120.
WEEKLY_MEANING = 60
WEEKLY_LISTENING = 30
WEEKLY_WRITING = 30


def build_weekly_test(words: list[dict], seed: int | None = None) -> list[dict]:
    return build_three_section_test(
        words=words,
        n_meaning=WEEKLY_MEANING,
        n_listening=WEEKLY_LISTENING,
        n_writing=WEEKLY_WRITING,
        seed=seed,
    )
