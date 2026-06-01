from typing import Literal, Optional
from sqlmodel import Field, SQLModel


class Word(SQLModel, table=True):
    __tablename__ = "words"

    id: str = Field(primary_key=True)
    word: str
    pinyin: str
    grade: int
    semester: int
    type: str = Field(sa_column_kwargs={"nullable": False})


class GradeMeta(SQLModel):
    grade: int
    semester: int
    label: str
    total: int
