import uuid
from typing import Optional

from sqlmodel import SQLModel


class QuizRequest(SQLModel):
    limit: int = 10
    grade: Optional[int] = None
    semester: Optional[int] = None


class QuizQuestion(SQLModel):
    word_id: str
    word: str
    options: list[str]
    # answer is intentionally withheld — revealed only in QuizResult


class QuizResponse(SQLModel):
    quiz_attempt_id: uuid.UUID
    questions: list[QuizQuestion]


class AnswerItem(SQLModel):
    word_id: str
    selected_answer: str


class QuizAnswerRequest(SQLModel):
    quiz_attempt_id: uuid.UUID
    answers: list[AnswerItem]


class QuizResult(SQLModel):
    word_id: str
    correct_answer: str
    selected_answer: str
    is_correct: bool


class QuizAnswerResponse(SQLModel):
    quiz_attempt_id: uuid.UUID
    score: int
    total: int
    results: list[QuizResult]
