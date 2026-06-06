"""
AI word explanation service using DeepSeek via the OpenAI-compatible API.
Fails gracefully if DEEPSEEK_API_KEY is absent or the provider is unavailable.
"""
import json
from datetime import datetime
from openai import AsyncOpenAI
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models.chat import WordExplanationCache
from app.schemas.chat import ExampleSentence, ExplainWordRequest, ExplainWordResponse

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"

_SYSTEM_PROMPT = """You are a Mandarin Chinese language teacher specialising in junior high curriculum vocabulary.

When given a Chinese word, respond with a JSON object containing exactly these fields:
- word: the Chinese word (string)
- pinyin: pinyin with tone marks (string)
- explanation_zh: a clear explanation in Chinese (中文解释) suited to the requested level (string)
- explanation: the same explanation in English suited to the requested level (string)
- examples: an array of exactly 3 objects, each with:
    - sentence: a Chinese sentence using the word (string)
    - translation: English translation of the sentence (string)
    - is_classical: true if the sentence is from Classical Chinese literature or uses classical grammar, false otherwise
- source_type: one of "说文解字", "其他古籍", or "通用解释" (string, optional but preferred)
- source_text: a short note about the source, etymology, or classical usage when available (string, optional but preferred)
- source_confidence: one of "high", "medium", or "low" (string, optional but preferred)
- When possible, prefer a 说文解字-based note for source_text. If you cannot confidently connect the word to 说文解字 or another classical source, do not fabricate a citation; use source_type="通用解释" and explain that the note is inferred from字形/词义.

Rules for the examples array:
1. The FIRST example must be a sentence from Classical Chinese (文言文) — ideally a well-known historical text such as 《论语》,《孟子》,《史记》,《古文观止》 or similar. Mark is_classical: true.
2. The SECOND example should be a natural modern written sentence. Mark is_classical: false.
3. The THIRD example should be a natural everyday spoken sentence. Mark is_classical: false.

Respond with raw JSON only — no markdown, no code block."""

_LEVEL_NOTES = {
    "beginner": "Use simple vocabulary. Keep the explanation under 2 sentences.",
    "intermediate": "Use clear language. Include useful context about usage.",
    "advanced": "Include nuance, register, and common collocations.",
}


def _normalize_key(value: str) -> str:
    return value.strip()


def _has_source_metadata(response: ExplainWordResponse) -> bool:
    return bool(response.source_type or response.source_text)


async def _get_cached_explanation(
    session: AsyncSession,
    request: ExplainWordRequest,
) -> ExplainWordResponse | None:
    stmt = select(WordExplanationCache).where(
        WordExplanationCache.word == _normalize_key(request.word),
        WordExplanationCache.level == request.level,
        WordExplanationCache.language == request.language,
    )
    result = await session.exec(stmt)
    cached = result.first()
    if not cached:
        return None

    try:
        response = ExplainWordResponse.model_validate(cached.response_json)
        if not _has_source_metadata(response):
            return None
        return response
    except Exception:
        return None


async def _save_cached_explanation(
    session: AsyncSession,
    request: ExplainWordRequest,
    response: ExplainWordResponse,
) -> None:
    payload = response.model_dump(mode="json")
    normalized_word = _normalize_key(request.word)

    stmt = select(WordExplanationCache).where(
        WordExplanationCache.word == normalized_word,
        WordExplanationCache.level == request.level,
        WordExplanationCache.language == request.language,
    )
    existing = (await session.exec(stmt)).first()
    if existing:
        existing.response_json = payload
        existing.model_name = MODEL
        existing.source = "ai"
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        session.add(
            WordExplanationCache(
                word=normalized_word,
                level=request.level,
                language=request.language,
                response_json=payload,
                model_name=MODEL,
                source="ai",
            )
        )

    await session.commit()


async def _generate_ai_explanation(request: ExplainWordRequest) -> ExplainWordResponse:
    if not settings.deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY is not configured")

    client = AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=DEEPSEEK_BASE_URL,
    )

    lang_note = "Respond in English." if request.language == "en" else "用中文回答。"
    level_note = _LEVEL_NOTES.get(request.level, "")

    user_prompt = (
        f"Explain the Chinese word: {request.word}\n"
        f"Level: {request.level}. {level_note}\n"
        f"{lang_note}"
    )

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    examples = [
        ExampleSentence(
            sentence=ex["sentence"],
            translation=ex["translation"],
            is_classical=ex.get("is_classical", False),
        )
        for ex in data.get("examples", [])
    ]

    return ExplainWordResponse(
        word=data["word"],
        pinyin=data["pinyin"],
        explanation_zh=data["explanation_zh"],
        explanation=data["explanation"],
        examples=examples,
        source_type=data.get("source_type"),
        source_text=data.get("source_text"),
        source_confidence=data.get("source_confidence"),
    )


async def explain_word(session: AsyncSession, request: ExplainWordRequest) -> ExplainWordResponse:
    try:
        cached = await _get_cached_explanation(session, request)
    except SQLAlchemyError:
        await session.rollback()
        cached = None

    if cached:
        return cached

    response = await _generate_ai_explanation(request)
    if not _has_source_metadata(response):
        response.source_type = "通用解释"
        response.source_text = "暂未可靠对应到《说文解字》条目，以下为根据字形、词义和常见用法整理的说明。"
        response.source_confidence = "low"
    try:
        await _save_cached_explanation(session, request, response)
    except SQLAlchemyError:
        await session.rollback()
    return response
