from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.quiz import QuizAnswerRequest, QuizAnswerResponse, QuizRequest, QuizResponse
from app.services import quiz as quiz_service

router = APIRouter(prefix="/quiz")


@router.post("", response_model=QuizResponse)
async def create_quiz(
    body: QuizRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await quiz_service.create_quiz(
            session, current_user.id, body.limit, body.grade, body.semester
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/answer", response_model=QuizAnswerResponse)
async def submit_answer(
    body: QuizAnswerRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await quiz_service.submit_quiz(
            session, current_user.id, body.quiz_attempt_id, body.answers
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
