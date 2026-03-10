from __future__ import annotations

from ai.test_generator import generate_mcq_test


def build_daily_test(words: list[dict], seed: int | None = None):
    return generate_mcq_test(words=words, n_questions=10, seed=seed)

