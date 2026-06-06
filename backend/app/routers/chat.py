from fastapi import APIRouter, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends

from app.db.session import get_session

from app.schemas.chat import ExplainWordRequest, ExplainWordResponse
from app.services import chat as chat_service

router = APIRouter(prefix="/chat")


@router.post("/explain-word", response_model=ExplainWordResponse)
async def explain_word(request: ExplainWordRequest, session: AsyncSession = Depends(get_session)):
    try:
        return await chat_service.explain_word(session, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI explanation service is temporarily unavailable",
        )
