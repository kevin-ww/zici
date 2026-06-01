import json
from pathlib import Path

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.word import Word

DATA_DIR = Path(__file__).parent.parent / "app" / "data"


async def _seed_words(session: AsyncSession):
    files = [
        "grade-7-1.json", "grade-7-2.json",
        "grade-8-1.json", "grade-8-2.json",
        "grade-9-1.json", "grade-9-2.json",
        "yicuo-words.json", "yicuo-idioms.json",
    ]
    for filename in files:
        for item in json.loads((DATA_DIR / filename).read_text()):
            existing = await session.get(Word, item["id"])
            if not existing:
                session.add(Word(**item))
    await session.commit()


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_grades(client):
    r = await client.get("/api/grades")
    assert r.status_code == 200
    grades = r.json()
    assert len(grades) == 8
    assert grades[0]["grade"] == 7
    assert grades[0]["semester"] == 1


@pytest.mark.asyncio
async def test_get_words_all(client, session):
    await _seed_words(session)
    r = await client.get("/api/words")
    assert r.status_code == 200
    words = r.json()
    assert len(words) > 0
    assert "id" in words[0]
    assert "word" in words[0]
    assert "pinyin" in words[0]


@pytest.mark.asyncio
async def test_get_words_filter_by_grade(client, session):
    await _seed_words(session)
    r = await client.get("/api/words?grade=7&semester=1")
    assert r.status_code == 200
    words = r.json()
    assert all(w["grade"] == 7 and w["semester"] == 1 for w in words)
    assert len(words) == 170


@pytest.mark.asyncio
async def test_get_words_includes_yicuo(client, session):
    await _seed_words(session)
    r = await client.get("/api/words")
    ids = {w["id"] for w in r.json()}
    assert any(wid.startswith("yc-") for wid in ids)
    assert any(wid.startswith("yi-") for wid in ids)


@pytest.mark.asyncio
async def test_get_word_by_id(client, session):
    await _seed_words(session)
    r = await client.get("/api/words/7-1-001")
    assert r.status_code == 200
    assert r.json()["id"] == "7-1-001"


@pytest.mark.asyncio
async def test_get_word_not_found(client):
    r = await client.get("/api/words/does-not-exist")
    assert r.status_code == 404
