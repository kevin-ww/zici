"""
Seed the database with all words and a demo user account.
Run with: uv run python scripts/seed_demo.py

Demo account:
  Email:    demo@zici.app
  Password: demo1234
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from app.core.config import settings
from app.core.security import hash_password

DATA_DIR = Path(__file__).parent.parent / "app" / "data"

WORD_FILES = [
    "grade-7-1.json",
    "grade-7-2.json",
    "grade-8-1.json",
    "grade-8-2.json",
    "grade-9-1.json",
    "grade-9-2.json",
    "yicuo-words.json",
    "yicuo-idioms.json",
]

DEMO_EMAIL = "demo@zici.app"
DEMO_PASSWORD = "demo1234"
DEMO_DISPLAY_NAME = "Demo User"


def _asyncpg_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def seed():
    connect_kwargs = {}
    if "6543" in settings.database_url:
        connect_kwargs["statement_cache_size"] = 0

    conn = await asyncpg.connect(_asyncpg_url(settings.database_url), **connect_kwargs)

    # --- words ---
    words = []
    for filename in WORD_FILES:
        for item in json.loads((DATA_DIR / filename).read_text()):
            words.append((
                item["id"], item["word"], item["pinyin"],
                item["grade"], item["semester"], item["type"],
            ))

    await conn.executemany(
        "INSERT INTO words (id, word, pinyin, grade, semester, type) "
        "VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (id) DO NOTHING",
        words,
    )
    print(f"Words: {len(words)} seeded.")

    # --- demo user ---
    existing = await conn.fetchval("SELECT id FROM users WHERE email = $1", DEMO_EMAIL)
    if existing:
        print(f"Demo user already exists: {DEMO_EMAIL}")
    else:
        hashed = hash_password(DEMO_PASSWORD)
        await conn.execute(
            "INSERT INTO users (email, display_name, hashed_password) VALUES ($1, $2, $3)",
            DEMO_EMAIL, DEMO_DISPLAY_NAME, hashed,
        )
        print(f"Demo user created: {DEMO_EMAIL} / {DEMO_PASSWORD}")

    # --- demo review queue: seed a few due cards for the demo user ---
    demo_user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", DEMO_EMAIL)
    first_words = await conn.fetch("SELECT id FROM words ORDER BY id LIMIT 5")
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    for row in first_words:
        await conn.execute(
            """
            INSERT INTO user_progress
              (user_id, word_id, status, repetitions, ease_factor, interval, next_review, wrong_count)
            VALUES ($1, $2, 'learning', 1, 2.5, 1, $3, 0)
            ON CONFLICT (user_id, word_id) DO UPDATE
              SET next_review = $3, status = 'learning'
            """,
            demo_user_id, row["id"], now,
        )
    print(f"Demo review queue: {len(first_words)} cards seeded as due.")

    await conn.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
