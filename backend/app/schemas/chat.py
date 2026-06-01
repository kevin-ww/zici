from typing import Literal, Optional
from sqlmodel import SQLModel


class ExplainWordRequest(SQLModel):
    word: str
    level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    language: Literal["en", "zh"] = "en"


class ExampleSentence(SQLModel):
    sentence: str
    translation: str
    is_classical: bool = False


class ExplainWordResponse(SQLModel):
    word: str
    pinyin: str
    explanation_zh: str
    explanation: str  # English
    examples: list[ExampleSentence]
