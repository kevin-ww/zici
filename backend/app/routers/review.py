from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.progress import ReviewEvent, UserProgress
from app.models.user import User
from app.models.word import Word
from app.schemas.progress import DueWordResponse, ProgressRead, ReviewAnswerRequest
from app.services import srs as srs_service

router = APIRouter(prefix="/review")


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


@router.get("/due", response_model=list[DueWordResponse])
async def get_due(
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    today = date.today()

    result = await session.exec(
        select(UserProgress, Word)
        .join(Word, Word.id == UserProgress.word_id)
        .where(
            UserProgress.user_id == current_user.id,
            (UserProgress.next_review == None) | (UserProgress.next_review <= today),
        )
        .limit(limit)
    )

    due = []
    for progress, word in result.all():
        due.append(DueWordResponse(
            id=word.id,
            word=word.word,
            pinyin=word.pinyin,
            grade=word.grade,
            semester=word.semester,
            type=word.type,
            progress=_to_read(progress),
        ))
    return due


@router.post("/answer", response_model=ProgressRead)
async def post_answer(
    body: ReviewAnswerRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    today = date.today()

    result = await session.exec(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.word_id == body.word_id,
        )
    )
    progress = result.first()

    if not progress:
        # first-time review — create default progress
        state = srs_service.get_default_progress(current_user.id, body.word_id)
    else:
        state = srs_service.ProgressState(
            user_id=progress.user_id,
            word_id=progress.word_id,
            status=progress.status,
            wrong_count=progress.wrong_count,
            last_reviewed=progress.last_reviewed,
            next_review=progress.next_review,
            ease_factor=float(progress.ease_factor),
            interval=progress.interval,
            repetitions=progress.repetitions,
        )

    prev_status = state.status
    prev_interval = state.interval
    prev_ease = state.ease_factor

    updated = srs_service.apply_review_answer(state, body.correct, today)

    if progress:
        progress.status = updated.status
        progress.wrong_count = updated.wrong_count
        progress.last_reviewed = updated.last_reviewed
        progress.next_review = updated.next_review
        progress.ease_factor = updated.ease_factor
        progress.interval = updated.interval
        progress.repetitions = updated.repetitions
        progress.updated_at = datetime.utcnow()
        session.add(progress)
    else:
        progress = UserProgress(
            user_id=current_user.id,
            word_id=body.word_id,
            status=updated.status,
            wrong_count=updated.wrong_count,
            last_reviewed=updated.last_reviewed,
            next_review=updated.next_review,
            ease_factor=updated.ease_factor,
            interval=updated.interval,
            repetitions=updated.repetitions,
        )
        session.add(progress)

    event = ReviewEvent(
        user_id=current_user.id,
        word_id=body.word_id,
        correct=body.correct,
        previous_status=prev_status,
        next_status=updated.status,
        previous_interval=prev_interval,
        next_interval=updated.interval,
        previous_ease_factor=prev_ease,
        next_ease_factor=updated.ease_factor,
    )
    session.add(event)
    await session.commit()
    await session.refresh(progress)

    return _to_read(progress)
