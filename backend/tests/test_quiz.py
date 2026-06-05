import pytest
from app.models.quiz import QuizPinyinDistractorSet
from app.models.word import Word
from app.services import quiz_distractors


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


@pytest.mark.asyncio
async def test_quiz_distractor_generation_prefers_same_length_candidates(session, monkeypatch):
    target = Word(id="q-target", word="通宵达旦", pinyin="tōng xiāo dá dàn", grade=9, semester=2, type="word")
    same_length_1 = Word(id="q-2", word="词二", pinyin="chén miǎn líng sǎn", grade=9, semester=2, type="word")
    same_length_2 = Word(id="q-3", word="词三", pinyin="hào hàn wú yín", grade=9, semester=2, type="word")
    same_length_3 = Word(id="q-4", word="词四", pinyin="chuí tóu sàng qì", grade=9, semester=2, type="word")
    other_1 = Word(id="q-5", word="词五", pinyin="qiān xǐ", grade=9, semester=2, type="word")
    other_2 = Word(id="q-6", word="词六", pinyin="yí rán", grade=9, semester=2, type="word")

    for w in [target, same_length_1, same_length_2, same_length_3, other_1, other_2]:
        if not await session.get(Word, w.id):
            session.add(w)
    await session.commit()

    async def fake_rank(target_word, target_pinyin, candidates):
        assert target_word == "通宵达旦"
        assert target_pinyin == "tōng xiāo dá dàn"
        assert all(quiz_distractors.syllable_count(item) == 4 for item in candidates)
        return None

    monkeypatch.setattr(quiz_distractors, "rank_distractors_with_ai", fake_rank)

    row = await quiz_distractors.get_or_create_distractor_set(
        session,
        target,
        [target, same_length_1, same_length_2, same_length_3, other_1, other_2],
    )
    assert row.word_id == target.id
    assert row.source == "rules"
    assert len(row.distractors_json) == 3
    assert all(quiz_distractors.syllable_count(opt) == 4 for opt in row.distractors_json)
    cached = await session.get(QuizPinyinDistractorSet, target.id)
    assert cached is not None


@pytest.mark.asyncio
async def test_quiz_distractor_cache_is_reused(session, monkeypatch):
    target = Word(id="q-cache", word="招徕", pinyin="zhāo lái", grade=9, semester=2, type="word")
    same_1 = Word(id="q-c1", word="词甲", pinyin="zhēng liè", grade=9, semester=2, type="word")
    same_2 = Word(id="q-c2", word="词乙", pinyin="zhāo lún", grade=9, semester=2, type="word")
    same_3 = Word(id="q-c3", word="词丙", pinyin="zhāng lǐ", grade=9, semester=2, type="word")

    for w in [target, same_1, same_2, same_3]:
        if not await session.get(Word, w.id):
            session.add(w)
    await session.commit()

    calls = {"count": 0}

    async def fake_rank(target_word, target_pinyin, candidates):
        calls["count"] += 1
        return list(candidates[:3])

    monkeypatch.setattr(quiz_distractors.settings, "quiz_ai_enabled", True)
    monkeypatch.setattr(quiz_distractors, "rank_distractors_with_ai", fake_rank)

    row1 = await quiz_distractors.get_or_create_distractor_set(session, target, [target, same_1, same_2, same_3])
    row2 = await quiz_distractors.get_or_create_distractor_set(session, target, [target, same_1, same_2, same_3])

    assert calls["count"] == 1
    assert row1.word_id == row2.word_id == target.id
    assert row1.distractors_json == row2.distractors_json
