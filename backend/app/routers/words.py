from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.models.word import GradeMeta, Word
from app.services import words as word_service

router = APIRouter()

_GRADE_INDEX: list[GradeMeta] = [
    GradeMeta(grade=7, semester=1, label="七年级上册", total=170),
    GradeMeta(grade=7, semester=2, label="七年级下册", total=137),
    GradeMeta(grade=8, semester=1, label="八年级上册", total=120),
    GradeMeta(grade=8, semester=2, label="八年级下册", total=105),
    GradeMeta(grade=9, semester=1, label="九年级上册", total=109),
    GradeMeta(grade=9, semester=2, label="九年级下册", total=108),
    GradeMeta(grade=9, semester=1, label="易错词语（专项）", total=174),
    GradeMeta(grade=9, semester=1, label="易错成语（专项）", total=160),
]


@router.get("/grades", response_model=list[GradeMeta])
async def get_grades():
    return _GRADE_INDEX


@router.get("/words", response_model=list[Word])
async def get_words(
    grade: int | None = Query(default=None),
    semester: int | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    return await word_service.get_all_words(session, grade, semester)


@router.get("/words/{word_id}", response_model=Word)
async def get_word(word_id: str, session: AsyncSession = Depends(get_session)):
    word = await word_service.get_word_by_id(session, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return word
