import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel


class WordExplanationCache(SQLModel, table=True):
    __tablename__ = "word_explanation_cache"
    __table_args__ = (
        UniqueConstraint("word", "level", "language", name="uq_word_explanation_cache_lookup"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    word: str = Field(index=True)
    level: str = Field(index=True)
    language: str = Field(index=True)
    response_json: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    model_name: str = Field(default="deepseek-chat")
    source: str = Field(default="ai")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
