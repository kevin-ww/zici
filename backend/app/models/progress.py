import uuid
from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UserProgress(SQLModel, table=True):
    __tablename__ = "user_progress"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    word_id: str = Field(foreign_key="words.id")
    status: str = Field(default="new")  # new | learning | mastered
    wrong_count: int = Field(default=0)
    last_reviewed: Optional[date] = None
    next_review: Optional[date] = None
    ease_factor: float = Field(default=2.5)
    interval: int = Field(default=1)
    repetitions: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # enforce unique(user_id, word_id) at the application level;
        # the DB constraint is added in the migration SQL
        pass


class ReviewEvent(SQLModel, table=True):
    __tablename__ = "review_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    word_id: str = Field(foreign_key="words.id")
    correct: bool
    previous_status: Optional[str] = None
    next_status: str
    previous_interval: Optional[int] = None
    next_interval: int
    previous_ease_factor: Optional[float] = None
    next_ease_factor: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
