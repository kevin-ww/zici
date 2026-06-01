from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ExplainWordRequest, ExplainWordResponse
from app.services import chat as chat_service

router = APIRouter(prefix="/chat")


@router.post("/explain-word", response_model=ExplainWordResponse)
async def explain_word(request: ExplainWordRequest):
    try:
        return await chat_service.explain_word(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI explanation service is temporarily unavailable",
        )
