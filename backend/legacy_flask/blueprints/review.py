from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from legacy_flask.blueprints.progress import _progress_store, _default_progress

review_bp = Blueprint("review", __name__)


def _apply_srs(progress: dict, correct: bool) -> dict:
    today = date.today().isoformat()

    if correct:
        progress["repetitions"] += 1
        if progress["repetitions"] == 1:
            progress["interval"] = 1
        elif progress["repetitions"] == 2:
            progress["interval"] = 6
        else:
            progress["interval"] = round(progress["interval"] * progress["ease_factor"])
        progress["ease_factor"] = max(1.3, progress["ease_factor"] + 0.1)
        progress["status"] = "mastered" if progress["repetitions"] >= 3 else "learning"
    else:
        progress["wrong_count"] += 1
        progress["repetitions"] = 0
        progress["interval"] = 1
        progress["ease_factor"] = max(1.3, progress["ease_factor"] - 0.2)
        progress["status"] = "learning"

    next_review = date.today() + timedelta(days=progress["interval"])
    progress["last_reviewed"] = today
    progress["next_review"] = next_review.isoformat()
    return progress


@review_bp.get("/review/due")
def get_due():
    today = date.today().isoformat()
    due = [
        p for p in _progress_store.values()
        if p["next_review"] is None or p["next_review"] <= today
    ]
    return jsonify(due)


@review_bp.post("/review/answer")
def post_answer():
    data = request.get_json()
    word_id = data["word_id"]
    correct = data["correct"]
    progress = _progress_store.get(word_id, _default_progress(word_id))
    updated = _apply_srs(progress, correct)
    _progress_store[word_id] = updated
    return jsonify(updated)
