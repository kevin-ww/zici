import json
from pathlib import Path

from flask import Blueprint, jsonify, request

words_bp = Blueprint("words", __name__)

DATA_DIR = Path(__file__).parent.parent.parent / "app" / "data"

GRADE_INDEX = [
    {"grade": 7, "semester": 1, "label": "七年级上册", "total": 170},
    {"grade": 7, "semester": 2, "label": "七年级下册", "total": 137},
    {"grade": 8, "semester": 1, "label": "八年级上册", "total": 120},
    {"grade": 8, "semester": 2, "label": "八年级下册", "total": 105},
    {"grade": 9, "semester": 1, "label": "九年级上册", "total": 109},
    {"grade": 9, "semester": 2, "label": "九年级下册", "total": 108},
]

WORD_FILES = {
    (7, 1): "grade-7-1.json",
    (7, 2): "grade-7-2.json",
    (8, 1): "grade-8-1.json",
    (8, 2): "grade-8-2.json",
    (9, 1): "grade-9-1.json",
    (9, 2): "grade-9-2.json",
}


def _load_all_words():
    words = []
    for filename in WORD_FILES.values():
        words.extend(json.loads((DATA_DIR / filename).read_text()))
    return words


@words_bp.get("/grades")
def get_grades():
    return jsonify(GRADE_INDEX)


@words_bp.get("/words")
def get_words():
    grade = request.args.get("grade", type=int)
    semester = request.args.get("semester", type=int)
    words = _load_all_words()
    if grade is not None:
        words = [w for w in words if w["grade"] == grade]
    if semester is not None:
        words = [w for w in words if w["semester"] == semester]
    return jsonify(words)


@words_bp.get("/words/<word_id>")
def get_word(word_id: str):
    for word in _load_all_words():
        if word["id"] == word_id:
            return jsonify(word)
    return jsonify({"detail": "Word not found"}), 404
