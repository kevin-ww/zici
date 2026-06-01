"""
Spaced repetition service — pure functions with no DB dependency.

Algorithm mirrors the original TypeScript markWord() in src/lib/storage.ts exactly.
All review dates are UTC. Parity tests in tests/test_parity.py verify this.
"""
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass
class ProgressState:
    user_id: uuid.UUID
    word_id: str
    status: str = "new"
    wrong_count: int = 0
    last_reviewed: Optional[date] = None
    next_review: Optional[date] = None
    ease_factor: float = 2.5
    interval: int = 1
    repetitions: int = 0


def get_default_progress(user_id: uuid.UUID, word_id: str) -> ProgressState:
    return ProgressState(user_id=user_id, word_id=word_id)


def apply_review_answer(
    progress: ProgressState,
    correct: bool,
    reviewed_at: date,
) -> ProgressState:
    """
    Apply one review answer and return updated progress.
    Does not mutate the input — returns a new ProgressState.
    """
    p = ProgressState(
        user_id=progress.user_id,
        word_id=progress.word_id,
        status=progress.status,
        wrong_count=progress.wrong_count,
        last_reviewed=progress.last_reviewed,
        next_review=progress.next_review,
        ease_factor=progress.ease_factor,
        interval=progress.interval,
        repetitions=progress.repetitions,
    )

    if correct:
        p.repetitions += 1
        if p.repetitions == 1:
            p.interval = 1
        elif p.repetitions == 2:
            p.interval = 6
        else:
            p.interval = round(p.interval * p.ease_factor)
        p.ease_factor = max(1.3, p.ease_factor + 0.1)
        p.status = "mastered" if p.repetitions >= 3 else "learning"
    else:
        p.wrong_count += 1
        p.repetitions = 0
        p.interval = 1
        p.ease_factor = max(1.3, p.ease_factor - 0.2)
        p.status = "learning"

    p.last_reviewed = reviewed_at
    p.next_review = reviewed_at + timedelta(days=p.interval)
    return p
