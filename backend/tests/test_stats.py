import pytest
from app.models.word import Word


async def _seed_words(session):
    words = [
        Word(id=f"7-1-{i:03d}", word=f"词{i}", pinyin=f"cí{i}", grade=7, semester=1, type="word")
        for i in range(1, 6)
    ] + [
        Word(id=f"8-1-{i:03d}", word=f"词{i+10}", pinyin=f"cí{i+10}", grade=8, semester=1, type="word")
        for i in range(1, 4)
    ]
    for w in words:
        existing = await session.get(Word, w.id)
        if not existing:
            session.add(w)
    await session.commit()


async def _register_and_login(client, email="stats@example.com"):
    await client.post("/api/auth/register", json={"email": email, "password": "password123"})
    r = await client.post("/api/auth/login", json={"email": email, "password": "password123"})
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_stats_requires_auth(client):
    r = await client.get("/api/stats/overview")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_overview_new_user(client, session):
    await _seed_words(session)
    token = await _register_and_login(client)
    r = await client.get("/api/stats/overview", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["mastered"] == 0
    assert body["learning"] == 0
    assert body["total"] == 8
    assert body["new_count"] == 8
    assert body["mastered_percent"] == 0.0


@pytest.mark.asyncio
async def test_overview_after_reviews(client, session):
    await _seed_words(session)
    token = await _register_and_login(client, "stats2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    # master one word (3 correct answers)
    for _ in range(3):
        await client.post("/api/review/answer", json={"word_id": "7-1-001", "correct": True}, headers=headers)
    # learning one word
    await client.post("/api/review/answer", json={"word_id": "7-1-002", "correct": True}, headers=headers)

    r = await client.get("/api/stats/overview", headers=headers)
    body = r.json()
    assert body["mastered"] == 1
    assert body["learning"] == 1
    assert body["new_count"] == 6


@pytest.mark.asyncio
async def test_by_grade_structure(client, session):
    await _seed_words(session)
    token = await _register_and_login(client, "stats3@example.com")
    r = await client.get("/api/stats/by-grade", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    grades = r.json()
    assert len(grades) == 2
    g71 = next(g for g in grades if g["grade"] == 7 and g["semester"] == 1)
    assert g71["total"] == 5
    assert g71["mastered"] == 0
    g81 = next(g for g in grades if g["grade"] == 8 and g["semester"] == 1)
    assert g81["total"] == 3


@pytest.mark.asyncio
async def test_summary_returns_both_concurrently(client, session):
    """GET /api/stats/summary uses asyncio.gather() to fetch overview and by-grade in parallel."""
    await _seed_words(session)
    token = await _register_and_login(client, "stats4@example.com")
    r = await client.get("/api/stats/summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert "overview" in body
    assert "by_grade" in body
    assert body["overview"]["total"] == 8
    assert isinstance(body["by_grade"], list)
    assert len(body["by_grade"]) == 2
