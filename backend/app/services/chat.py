"""
AI word explanation service using DeepSeek via the OpenAI-compatible API.
Fails gracefully if DEEPSEEK_API_KEY is absent or the provider is unavailable.
"""
import json

from openai import AsyncOpenAI

from app.core.config import settings
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


async def explain_word(request: ExplainWordRequest) -> ExplainWordResponse:
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
    )
