from __future__ import annotations

from ai.test_generator import build_three_section_test


# Final: all 300 words. TOCFL-scale. Meaning 100, Listening 50, Writing 50. Total 200.
FINAL_MEANING = 100
FINAL_LISTENING = 50
FINAL_WRITING = 50


def build_final_test(words: list[dict], seed: int | None = None) -> list[dict]:
    return build_three_section_test(
        words=words,
        n_meaning=FINAL_MEANING,
        n_listening=FINAL_LISTENING,
        n_writing=FINAL_WRITING,
        seed=seed,
    )
