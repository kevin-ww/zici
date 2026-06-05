import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from app.main import app
from app.db.session import get_session
# import all models so SQLModel.metadata is populated
from app.models.word import Word  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.progress import UserProgress, ReviewEvent  # noqa: F401
from app.models.quiz import QuizAttempt, QuizAnswer, QuizPinyinDistractorSet  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as s:
        yield s
        await s.exec(text("DELETE FROM quiz_answers"))
        await s.exec(text("DELETE FROM quiz_attempts"))
        await s.exec(text("DELETE FROM quiz_pinyin_distractor_sets"))
        await s.exec(text("DELETE FROM review_events"))
        await s.exec(text("DELETE FROM user_progress"))
        await s.exec(text("DELETE FROM users"))
        await s.exec(text("DELETE FROM words"))
        await s.commit()


@pytest_asyncio.fixture
async def client(session):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
