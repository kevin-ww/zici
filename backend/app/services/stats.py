import uuid
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.progress import UserProgress
from app.models.word import Word
from app.schemas.stats import StatsByGrade, StatsOverview


async def get_overview(session: AsyncSession, user_id: uuid.UUID) -> StatsOverview:
    # total words in catalog
    total = (await session.exec(select(func.count()).select_from(Word))).one()

    result = await session.exec(
        select(UserProgress).where(UserProgress.user_id == user_id)
    )
    all_progress = result.all()

    mastered = sum(1 for p in all_progress if p.status == "mastered")
    learning = sum(1 for p in all_progress if p.status == "learning")
    new_count = total - mastered - learning
    mastered_percent = round((mastered / total * 100) if total else 0, 1)

    return StatsOverview(
        total=total,
        mastered=mastered,
        learning=learning,
        new_count=new_count,
        mastered_percent=mastered_percent,
    )


async def get_by_grade(session: AsyncSession, user_id: uuid.UUID) -> list[StatsByGrade]:
    # get total words per grade/semester from catalog
    grade_totals_result = await session.exec(
        select(Word.grade, Word.semester, func.count().label("total"))
        .group_by(Word.grade, Word.semester)
        .order_by(Word.grade, Word.semester)
    )
    grade_totals = {(r.grade, r.semester): r.total for r in grade_totals_result.all()}

    # get progress counts per grade/semester
    progress_result = await session.exec(
        select(Word.grade, Word.semester, UserProgress.status, func.count().label("cnt"))
        .join(UserProgress, UserProgress.word_id == Word.id)
        .where(UserProgress.user_id == user_id)
        .group_by(Word.grade, Word.semester, UserProgress.status)
    )

    progress_map: dict[tuple, dict] = {}
    for row in progress_result.all():
        key = (row.grade, row.semester)
        if key not in progress_map:
            progress_map[key] = {"mastered": 0, "learning": 0}
        progress_map[key][row.status] = row.cnt

    stats = []
    for (grade, semester), total in sorted(grade_totals.items()):
        p = progress_map.get((grade, semester), {})
        mastered = p.get("mastered", 0)
        learning = p.get("learning", 0)
        new_count = total - mastered - learning
        stats.append(StatsByGrade(
            grade=grade,
            semester=semester,
            total=total,
            mastered=mastered,
            learning=learning,
            new_count=new_count,
            mastered_percent=round((mastered / total * 100) if total else 0, 1),
        ))

    return stats
