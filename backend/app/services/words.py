from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.word import Word


async def get_all_words(session: AsyncSession, grade: int | None, semester: int | None) -> list[Word]:
    stmt = select(Word)
    if grade is not None:
        stmt = stmt.where(Word.grade == grade)
    if semester is not None:
        stmt = stmt.where(Word.semester == semester)
    result = await session.exec(stmt)
    return result.all()


async def get_word_by_id(session: AsyncSession, word_id: str) -> Word | None:
    return await session.get(Word, word_id)
