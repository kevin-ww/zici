"""
Parity tests: assert the Python SRS service produces identical results
to the original TypeScript markWord() in src/lib/storage.ts.

Each fixture is a (initial_state, correct, expected_state) triple
derived directly from the TypeScript algorithm.
"""
import uuid
from datetime import date

import pytest

from app.services.srs import ProgressState, apply_review_answer

TODAY = date(2026, 5, 30)
USER_ID = uuid.uuid4()
WORD_ID = "7-1-001"


def state(**kwargs) -> ProgressState:
    defaults = dict(
        user_id=USER_ID, word_id=WORD_ID,
        status="new", wrong_count=0,
        ease_factor=2.5, interval=1, repetitions=0,
        last_reviewed=None, next_review=None,
    )
    defaults.update(kwargs)
    return ProgressState(**defaults)


# --- correct answer cases (mirrors markWord(wordId, true)) ---

def test_parity_rep0_correct():
    """repetitions 0→1, interval stays 1, status→learning"""
    r = apply_review_answer(state(repetitions=0), correct=True, reviewed_at=TODAY)
    assert r.repetitions == 1
    assert r.interval == 1
    assert r.status == "learning"
    assert r.ease_factor == pytest.approx(2.6)
    assert r.next_review == date(2026, 5, 31)


def test_parity_rep1_correct():
    """repetitions 1→2, interval→6, status still learning"""
    r = apply_review_answer(state(repetitions=1, interval=1, ease_factor=2.6), correct=True, reviewed_at=TODAY)
    assert r.repetitions == 2
    assert r.interval == 6
    assert r.status == "learning"
    assert r.ease_factor == pytest.approx(2.7)
    assert r.next_review == date(2026, 6, 5)


def test_parity_rep2_correct():
    """repetitions 2→3, interval=round(6*2.7)=16, status→mastered"""
    r = apply_review_answer(state(repetitions=2, interval=6, ease_factor=2.7), correct=True, reviewed_at=TODAY)
    assert r.repetitions == 3
    assert r.interval == round(6 * 2.7)
    assert r.status == "mastered"
    assert r.ease_factor == pytest.approx(2.8)


# --- wrong answer cases (mirrors markWord(wordId, false)) ---

def test_parity_wrong_from_new():
    """wrong on new word: wrong_count→1, reps reset to 0, interval reset to 1"""
    r = apply_review_answer(state(), correct=False, reviewed_at=TODAY)
    assert r.wrong_count == 1
    assert r.repetitions == 0
    assert r.interval == 1
    assert r.status == "learning"
    assert r.ease_factor == pytest.approx(2.3)
    assert r.next_review == date(2026, 5, 31)


def test_parity_wrong_from_learning():
    """wrong on learning word resets all SRS counters"""
    r = apply_review_answer(
        state(status="learning", repetitions=2, interval=6, ease_factor=2.7),
        correct=False, reviewed_at=TODAY,
    )
    assert r.repetitions == 0
    assert r.interval == 1
    assert r.ease_factor == pytest.approx(2.5)
    assert r.status == "learning"


def test_parity_wrong_at_ease_floor():
    """ease factor cannot drop below 1.3 regardless of wrong streak"""
    p = state(ease_factor=1.3)
    r = apply_review_answer(p, correct=False, reviewed_at=TODAY)
    assert r.ease_factor == pytest.approx(1.3)


# --- alternating sequence ---

def test_parity_alternating_sequence():
    """
    Sequence: correct, correct, wrong, correct, correct, correct
    Mirrors running markWord 6 times with the above pattern.
    """
    p = state()
    p = apply_review_answer(p, correct=True,  reviewed_at=TODAY)  # rep=1, interval=1
    p = apply_review_answer(p, correct=True,  reviewed_at=TODAY)  # rep=2, interval=6
    p = apply_review_answer(p, correct=False, reviewed_at=TODAY)  # rep=0, interval=1, ef-=0.2
    p = apply_review_answer(p, correct=True,  reviewed_at=TODAY)  # rep=1, interval=1
    p = apply_review_answer(p, correct=True,  reviewed_at=TODAY)  # rep=2, interval=6
    p = apply_review_answer(p, correct=True,  reviewed_at=TODAY)  # rep=3, mastered

    # trace: ef=2.5 → +0.1 → +0.1 → -0.2 → +0.1 → +0.1 → +0.1 = 2.8
    # intervals: 1, 6, reset, 1, 6, round(6*2.7)=16
    assert p.status == "mastered"
    assert p.repetitions == 3
    assert p.wrong_count == 1
    assert p.interval == round(6 * 2.7)  # = 16
    assert p.ease_factor == pytest.approx(2.8)
