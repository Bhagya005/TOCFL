from __future__ import annotations

from dataclasses import dataclass
from datetime import date


WORDS_PER_DAY = 15
TOTAL_DAYS = 20
TOTAL_WORDS = 300


@dataclass(frozen=True)
class StudyPlan:
    current_day: int
    unlocked_upto_word_id: int


def compute_study_plan(start_date: date, today: date | None = None) -> StudyPlan:
    today = today or date.today()
    delta_days = (today - start_date).days
    current_day = max(1, min(TOTAL_DAYS, delta_days + 1))
    unlocked_upto = min(TOTAL_WORDS, current_day * WORDS_PER_DAY)
    return StudyPlan(current_day=current_day, unlocked_upto_word_id=unlocked_upto)


def day_word_range(day: int) -> tuple[int, int]:
    day = max(1, min(TOTAL_DAYS, day))
    start_id = (day - 1) * WORDS_PER_DAY + 1
    end_id = min(TOTAL_WORDS, day * WORDS_PER_DAY)
    return start_id, end_id


def week_word_upto(day: int) -> int:
    """
    Weekly checkpoints:
    - day 7  -> 105 words
    - day 14 -> 210 words
    - day 20 -> 300 words
    """
    if day >= 20:
        return 300
    if day >= 14:
        return 210
    if day >= 7:
        return 105
    return min(300, day * WORDS_PER_DAY)

