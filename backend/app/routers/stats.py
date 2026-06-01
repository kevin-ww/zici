import asyncio

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.stats import StatsByGrade, StatsOverview
from app.services import stats as stats_service

router = APIRouter(prefix="/stats")


@router.get("/overview", response_model=StatsOverview)
async def get_overview(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await stats_service.get_overview(session, current_user.id)


@router.get("/by-grade", response_model=list[StatsByGrade])
async def get_by_grade(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await stats_service.get_by_grade(session, current_user.id)


@router.get("/summary", response_model=dict)
async def get_summary(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Returns overview and by-grade stats in a single request.
    Uses asyncio.gather() to fetch both concurrently — total time ≈ max(query_a, query_b)
    instead of query_a + query_b if run sequentially.
    """
    overview, by_grade = await asyncio.gather(
        stats_service.get_overview(session, current_user.id),
        stats_service.get_by_grade(session, current_user.id),
    )
    return {
        "overview": overview.model_dump(),
        "by_grade": [g.model_dump() for g in by_grade],
    }
