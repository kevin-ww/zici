import pytest


async def _register_and_login(client, email="reviewer@example.com", password="password123"):
    await client.post("/api/auth/register", json={"email": email, "password": password})
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_due_requires_auth(client):
    r = await client.get("/api/review/due")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_answer_requires_auth(client):
    r = await client.post("/api/review/answer", json={"word_id": "7-1-001", "correct": True})
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_due_empty_for_new_user(client):
    token = await _register_and_login(client)
    r = await client.get("/api/review/due", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_answer_creates_progress(client):
    token = await _register_and_login(client)
    r = await client.post(
        "/api/review/answer",
        json={"word_id": "7-1-001", "correct": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["word_id"] == "7-1-001"
    assert body["status"] == "learning"
    assert body["repetitions"] == 1
    assert body["interval"] == 1
    assert body["ease_factor"] == pytest.approx(2.6)


@pytest.mark.asyncio
async def test_answer_wrong_resets_progress(client):
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    # two correct answers first
    for _ in range(2):
        await client.post("/api/review/answer", json={"word_id": "7-1-001", "correct": True}, headers=headers)
    # then wrong
    r = await client.post("/api/review/answer", json={"word_id": "7-1-001", "correct": False}, headers=headers)
    body = r.json()
    assert body["repetitions"] == 0
    assert body["interval"] == 1
    assert body["wrong_count"] == 1


@pytest.mark.asyncio
async def test_three_correct_answers_mastered(client):
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(3):
        r = await client.post("/api/review/answer", json={"word_id": "7-1-001", "correct": True}, headers=headers)
    assert r.json()["status"] == "mastered"


@pytest.mark.asyncio
async def test_progress_scoped_to_user(client):
    """Two users reviewing the same word get independent progress records."""
    token_a = await _register_and_login(client, "user_a@example.com")
    token_b = await _register_and_login(client, "user_b@example.com")

    await client.post(
        "/api/review/answer",
        json={"word_id": "7-1-001", "correct": True},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    r = await client.get(
        "/api/progress/7-1-001",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 404  # user B has no progress yet


@pytest.mark.asyncio
async def test_due_returns_words_after_answer(client, session):
    """Words answered today (interval=1) appear in due queue the next day."""
    from datetime import date, timedelta
    from app.models.progress import UserProgress
    from app.models.word import Word
    from sqlmodel import select

    # seed one word into the test DB
    w = await session.get(Word, "7-1-001")
    if not w:
        session.add(Word(id="7-1-001", word="示例", pinyin="shì lì", grade=7, semester=1, type="word"))
        await session.commit()

    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # answer — creates progress with next_review = today + 1
    await client.post("/api/review/answer", json={"word_id": "7-1-001", "correct": True}, headers=headers)

    # backdate next_review to today so it counts as due
    result = await session.exec(select(UserProgress).where(UserProgress.word_id == "7-1-001"))
    p = result.first()
    assert p is not None
    p.next_review = date.today()
    session.add(p)
    await session.commit()
    await session.refresh(p)

    r = await client.get("/api/review/due", headers=headers)
    assert r.status_code == 200
    ids = [w["id"] for w in r.json()]
    assert "7-1-001" in ids
