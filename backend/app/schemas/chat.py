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
    source_type: Optional[Literal["说文解字", "其他古籍", "通用解释"]] = None
    source_text: Optional[str] = None
    source_confidence: Optional[Literal["high", "medium", "low"]] = None
