import uuid
from datetime import date
from typing import Optional

from sqlmodel import SQLModel


class ProgressRead(SQLModel):
    word_id: str
    status: str
    wrong_count: int
    last_reviewed: Optional[date]
    next_review: Optional[date]
    ease_factor: float
    interval: int
    repetitions: int


class ReviewAnswerRequest(SQLModel):
    word_id: str
    correct: bool


class DueWordResponse(SQLModel):
    id: str
    word: str
    pinyin: str
    grade: int
    semester: int
    type: str
    progress: ProgressRead
