"""
Chat endpoint tests — the DeepSeek API is mocked so tests run without a live key.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import select

from app.models.chat import WordExplanationCache


def _mock_deepseek_response(word="矛盾", pinyin="máo dùn"):
    content = json.dumps({
        "word": word,
        "pinyin": pinyin,
        "explanation_zh": "矛盾指两种事物或观点相互对立、不能并存的状态。",
        "explanation": "A contradiction or conflict between ideas.",
        "examples": [
            {
                "sentence": "自相矛盾，不可并立。",
                "translation": "A self-contradiction cannot stand at the same time.",
                "is_classical": True,
            },
            {
                "sentence": "他的说法前后矛盾，让人难以信服。",
                "translation": "His statements are contradictory and hard to believe.",
                "is_classical": False,
            },
            {
                "sentence": "你说的和做的完全矛盾嘛！",
                "translation": "What you say and what you do are completely contradictory!",
                "is_classical": False,
            },
        ],
    })
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.mark.asyncio
async def test_explain_word_success(client):
    mock_response = _mock_deepseek_response()
    with patch("app.services.chat.AsyncOpenAI") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_instance

        with patch("app.services.chat.settings") as mock_settings:
            mock_settings.deepseek_api_key = "test-key"
            r = await client.post("/api/chat/explain-word", json={"word": "矛盾"})

    assert r.status_code == 200
    body = r.json()
    assert body["word"] == "矛盾"
    assert body["pinyin"] == "máo dùn"
    assert "explanation_zh" in body
    assert "explanation" in body
    assert "examples" in body
    assert len(body["examples"]) == 3

    # First example must be classical
    assert body["examples"][0]["is_classical"] is True
    # Others are modern
    assert body["examples"][1]["is_classical"] is False
    assert body["examples"][2]["is_classical"] is False

    # All examples have required fields
    for ex in body["examples"]:
        assert "sentence" in ex
        assert "translation" in ex
        assert "is_classical" in ex


@pytest.mark.asyncio
async def test_explain_word_no_api_key(client):
    with patch("app.services.chat.settings") as mock_settings:
        mock_settings.deepseek_api_key = ""
        r = await client.post("/api/chat/explain-word", json={"word": "矛盾"})
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"]


@pytest.mark.asyncio
async def test_explain_word_provider_unavailable(client):
    with patch("app.services.chat.AsyncOpenAI") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(side_effect=Exception("connection error"))
        mock_client_cls.return_value = mock_instance

        with patch("app.services.chat.settings") as mock_settings:
            mock_settings.deepseek_api_key = "test-key"
            r = await client.post("/api/chat/explain-word", json={"word": "矛盾"})

    assert r.status_code == 503
    assert "temporarily unavailable" in r.json()["detail"]


@pytest.mark.asyncio
async def test_explain_word_level_and_language(client):
    mock_response = _mock_deepseek_response()
    with patch("app.services.chat.AsyncOpenAI") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_instance

        with patch("app.services.chat.settings") as mock_settings:
            mock_settings.deepseek_api_key = "test-key"
            r = await client.post("/api/chat/explain-word", json={
                "word": "矛盾",
                "level": "beginner",
                "language": "zh",
            })

    assert r.status_code == 200


@pytest.mark.asyncio
async def test_explain_word_cache_reused_without_ai(client, session):
    mock_response = _mock_deepseek_response()
    with patch("app.services.chat.AsyncOpenAI") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_instance

        with patch("app.services.chat.settings") as mock_settings:
            mock_settings.deepseek_api_key = "test-key"
            first = await client.post("/api/chat/explain-word", json={"word": "矛盾"})
            assert first.status_code == 200

            mock_settings.deepseek_api_key = ""
            second = await client.post("/api/chat/explain-word", json={"word": "矛盾"})

    assert second.status_code == 200
    assert mock_client_cls.call_count == 1
    assert mock_instance.chat.completions.create.call_count == 1

    result = await session.exec(
        select(WordExplanationCache).where(
            WordExplanationCache.word == "矛盾",
            WordExplanationCache.level == "intermediate",
            WordExplanationCache.language == "en",
        )
    )
    cached = result.first()
    assert cached is not None
    assert cached.response_json["word"] == "矛盾"
    assert cached.response_json["pinyin"] == "máo dùn"
    assert cached.response_json["examples"][0]["is_classical"] is True
