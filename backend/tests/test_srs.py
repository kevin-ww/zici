"""
Unit tests for the SRS service — no DB, no HTTP.
"""
import uuid
from datetime import date

import pytest

from app.services.srs import ProgressState, apply_review_answer, get_default_progress


TODAY = date(2026, 5, 30)
USER_ID = uuid.uuid4()
WORD_ID = "7-1-001"


def test_default_progress():
    p = get_default_progress(USER_ID, WORD_ID)
    assert p.status == "new"
    assert p.wrong_count == 0
    assert p.ease_factor == 2.5
    assert p.interval == 1
    assert p.repetitions == 0
    assert p.last_reviewed is None
    assert p.next_review is None


def test_first_correct_sets_interval_1():
    p = get_default_progress(USER_ID, WORD_ID)
    r = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    assert r.repetitions == 1
    assert r.interval == 1
    assert r.status == "learning"
    assert r.last_reviewed == TODAY
    assert r.next_review == date(2026, 5, 31)


def test_second_correct_sets_interval_6():
    p = get_default_progress(USER_ID, WORD_ID)
    p = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    p = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    assert p.repetitions == 2
    assert p.interval == 6
    assert p.status == "learning"  # boundary: still learning at rep 2


def test_third_correct_sets_mastered():
    p = get_default_progress(USER_ID, WORD_ID)
    for _ in range(3):
        p = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    assert p.repetitions == 3
    assert p.status == "mastered"  # boundary: mastered at rep 3


def test_fourth_correct_uses_ease_factor():
    p = get_default_progress(USER_ID, WORD_ID)
    for _ in range(3):
        p = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    # after 3 correct: interval=16, ease_factor=2.8
    p = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    assert p.interval == round(16 * 2.8)  # = 45
    assert p.repetitions == 4


def test_ease_factor_increases_on_correct():
    p = get_default_progress(USER_ID, WORD_ID)
    p = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    assert p.ease_factor == pytest.approx(2.6)


def test_ease_factor_floor_on_correct():
    p = ProgressState(user_id=USER_ID, word_id=WORD_ID, ease_factor=1.3)
    p = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    assert p.ease_factor == pytest.approx(1.4)  # floor only prevents going below 1.3


def test_wrong_resets_repetitions():
    p = get_default_progress(USER_ID, WORD_ID)
    p = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    p = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    p = apply_review_answer(p, correct=False, reviewed_at=TODAY)
    assert p.repetitions == 0
    assert p.interval == 1
    assert p.status == "learning"
    assert p.wrong_count == 1


def test_wrong_decreases_ease_factor():
    p = get_default_progress(USER_ID, WORD_ID)
    p = apply_review_answer(p, correct=False, reviewed_at=TODAY)
    assert p.ease_factor == pytest.approx(2.3)


def test_ease_factor_floor_on_wrong():
    p = ProgressState(user_id=USER_ID, word_id=WORD_ID, ease_factor=1.4)
    p = apply_review_answer(p, correct=False, reviewed_at=TODAY)
    assert p.ease_factor == pytest.approx(1.3)


def test_ease_factor_does_not_go_below_floor():
    p = ProgressState(user_id=USER_ID, word_id=WORD_ID, ease_factor=1.3)
    p = apply_review_answer(p, correct=False, reviewed_at=TODAY)
    assert p.ease_factor == pytest.approx(1.3)


def test_does_not_mutate_input():
    p = get_default_progress(USER_ID, WORD_ID)
    _ = apply_review_answer(p, correct=True, reviewed_at=TODAY)
    assert p.repetitions == 0  # original unchanged
