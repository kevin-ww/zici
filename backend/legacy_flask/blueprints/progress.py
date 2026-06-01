from flask import Blueprint, jsonify, request, g

progress_bp = Blueprint("progress", __name__)


# In the Flask version, progress is stored in-process (no database).
# This mirrors what the frontend did with IndexedDB — no persistence across restarts.
# The FastAPI version replaces this with Supabase-backed user_progress rows.
_progress_store: dict[str, dict] = {}


def _default_progress(word_id: str) -> dict:
    return {
        "word_id": word_id,
        "status": "new",
        "wrong_count": 0,
        "last_reviewed": None,
        "next_review": None,
        "ease_factor": 2.5,
        "interval": 1,
        "repetitions": 0,
    }


@progress_bp.get("/progress")
def get_all_progress():
    return jsonify(list(_progress_store.values()))


@progress_bp.get("/progress/<word_id>")
def get_progress(word_id: str):
    return jsonify(_progress_store.get(word_id, _default_progress(word_id)))


@progress_bp.put("/progress/<word_id>")
def update_progress(word_id: str):
    data = request.get_json()
    _progress_store[word_id] = data
    return jsonify(data)
