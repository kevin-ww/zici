import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class QuizAttempt(SQLModel, table=True):
    __tablename__ = "quiz_attempts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    score: Optional[int] = None
    total: int
    grade: Optional[int] = None
    semester: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuizAnswer(SQLModel, table=True):
    __tablename__ = "quiz_answers"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    quiz_attempt_id: uuid.UUID = Field(foreign_key="quiz_attempts.id", index=True)
    word_id: str = Field(foreign_key="words.id")
    selected_answer: str
    correct_answer: str
    is_correct: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
