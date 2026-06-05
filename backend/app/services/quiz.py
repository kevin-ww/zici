import random
import uuid
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.quiz import QuizAnswer, QuizAttempt
from app.models.word import Word
from app.schemas.quiz import (
    AnswerItem,
    QuizAnswerResponse,
    QuizQuestion,
    QuizResponse,
    QuizResult,
)
from app.services.quiz_distractors import get_or_create_distractor_set


async def create_quiz(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int,
    grade: Optional[int],
    semester: Optional[int],
) -> QuizResponse:
    stmt = select(Word)
    if grade is not None:
        stmt = stmt.where(Word.grade == grade)
    if semester is not None:
        stmt = stmt.where(Word.semester == semester)

    result = await session.exec(stmt)
    all_words = result.all()

    if len(all_words) < 4:
        raise ValueError("Not enough words to generate a quiz (need at least 4)")

    selected = random.sample(all_words, min(limit, len(all_words)))

    questions = []
    for word in selected:
        distractor_set = await get_or_create_distractor_set(session, word, all_words)
        distractors = list(distractor_set.distractors_json)
        options = distractors + [word.pinyin]
        random.shuffle(options)
        questions.append(QuizQuestion(
            word_id=word.id,
            word=word.word,
            options=options,
        ))

    attempt = QuizAttempt(user_id=user_id, total=len(questions))
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)

    return QuizResponse(quiz_attempt_id=attempt.id, questions=questions)


async def submit_quiz(
    session: AsyncSession,
    user_id: uuid.UUID,
    attempt_id: uuid.UUID,
    answers: list[AnswerItem],
) -> QuizAnswerResponse:
    attempt = await session.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != user_id:
        raise ValueError("Quiz attempt not found")

    results = []
    score = 0

    for answer in answers:
        word = await session.get(Word, answer.word_id)
        if not word:
            continue
        is_correct = answer.selected_answer == word.pinyin
        if is_correct:
            score += 1
        session.add(QuizAnswer(
            quiz_attempt_id=attempt_id,
            word_id=answer.word_id,
            selected_answer=answer.selected_answer,
            correct_answer=word.pinyin,
            is_correct=is_correct,
        ))
        results.append(QuizResult(
            word_id=answer.word_id,
            correct_answer=word.pinyin,
            selected_answer=answer.selected_answer,
            is_correct=is_correct,
        ))

    attempt.score = score
    session.add(attempt)
    await session.commit()

    return QuizAnswerResponse(
        quiz_attempt_id=attempt_id,
        score=score,
        total=len(results),
        results=results,
    )
