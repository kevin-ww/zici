import pytest
from app.models.word import Word


async def _seed_words(session, count=20):
    for i in range(1, count + 1):
        w = Word(id=f"q-{i:03d}", word=f"词{i}", pinyin=f"pīnyīn{i}", grade=7, semester=1, type="word")
        existing = await session.get(Word, w.id)
        if not existing:
            session.add(w)
    await session.commit()


async def _register_and_login(client, email="quiz@example.com"):
    await client.post("/api/auth/register", json={"email": email, "password": "password123"})
    r = await client.post("/api/auth/login", json={"email": email, "password": "password123"})
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_quiz_requires_auth(client):
    r = await client.post("/api/quiz", json={"limit": 5})
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_quiz(client, session):
    await _seed_words(session)
    token = await _register_and_login(client)
    r = await client.post("/api/quiz", json={"limit": 5}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert "quiz_attempt_id" in body
    assert len(body["questions"]) == 5
    q = body["questions"][0]
    assert "word_id" in q
    assert "word" in q
    assert len(q["options"]) == 4
    # answer must NOT be in the quiz response
    assert "answer" not in q


@pytest.mark.asyncio
async def test_quiz_options_include_correct_answer(client, session):
    await _seed_words(session)
    token = await _register_and_login(client, "quiz2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.post("/api/quiz", json={"limit": 5}, headers=headers)
    questions = r.json()["questions"]

    for q in questions:
        # fetch the word to verify the correct pinyin is among the options
        word_r = await client.get(f"/api/words/{q['word_id']}")
        correct_pinyin = word_r.json()["pinyin"]
        assert correct_pinyin in q["options"]


@pytest.mark.asyncio
async def test_quiz_answer_scores_correctly(client, session):
    await _seed_words(session)
    token = await _register_and_login(client, "quiz3@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    quiz_r = await client.post("/api/quiz", json={"limit": 3}, headers=headers)
    body = quiz_r.json()
    attempt_id = body["quiz_attempt_id"]
    questions = body["questions"]

    # look up correct answers, answer all correctly
    answers = []
    for q in questions:
        word_r = await client.get(f"/api/words/{q['word_id']}")
        answers.append({"word_id": q["word_id"], "selected_answer": word_r.json()["pinyin"]})

    r = await client.post(
        "/api/quiz/answer",
        json={"quiz_attempt_id": attempt_id, "answers": answers},
        headers=headers,
    )
    assert r.status_code == 200
    result = r.json()
    assert result["score"] == 3
    assert result["total"] == 3
    assert all(res["is_correct"] for res in result["results"])
    assert all("correct_answer" in res for res in result["results"])


@pytest.mark.asyncio
async def test_quiz_answer_wrong_attempt_id(client, session):
    await _seed_words(session)
    token = await _register_and_login(client, "quiz4@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    import uuid
    r = await client.post(
        "/api/quiz/answer",
        json={"quiz_attempt_id": str(uuid.uuid4()), "answers": []},
        headers=headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_quiz_filter_by_grade(client, session):
    await _seed_words(session)
    token = await _register_and_login(client, "quiz5@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.post("/api/quiz", json={"limit": 5, "grade": 7, "semester": 1}, headers=headers)
    assert r.status_code == 200
    assert len(r.json()["questions"]) == 5
