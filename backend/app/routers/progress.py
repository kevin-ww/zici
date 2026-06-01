from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.progress import UserProgress
from app.models.user import User
from app.schemas.progress import ProgressRead

router = APIRouter(prefix="/progress")


def _to_read(p: UserProgress) -> ProgressRead:
    return ProgressRead(
        word_id=p.word_id,
        status=p.status,
        wrong_count=p.wrong_count,
        last_reviewed=p.last_reviewed,
        next_review=p.next_review,
        ease_factor=p.ease_factor,
        interval=p.interval,
        repetitions=p.repetitions,
    )


@router.get("", response_model=list[ProgressRead])
async def get_all_progress(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.exec(
        select(UserProgress).where(UserProgress.user_id == current_user.id)
    )
    return [_to_read(p) for p in result.all()]


@router.get("/{word_id}", response_model=ProgressRead)
async def get_progress(
    word_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.exec(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.word_id == word_id,
        )
    )
    p = result.first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found")
    return _to_read(p)
