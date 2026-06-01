"""
Seed the words table from the JSON data files.
Run with: uv run python scripts/seed.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from app.core.config import settings

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


def _asyncpg_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def seed():
    conn = await asyncpg.connect(_asyncpg_url(settings.database_url), statement_cache_size=0)

    words = []
    for filename in WORD_FILES:
        for item in json.loads((DATA_DIR / filename).read_text()):
            words.append((item["id"], item["word"], item["pinyin"], item["grade"], item["semester"], item["type"]))

    inserted = await conn.executemany(
        """
        INSERT INTO words (id, word, pinyin, grade, semester, type)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (id) DO NOTHING
        """,
        words,
    )
    await conn.close()
    print(f"Seeded {len(words)} words.")


if __name__ == "__main__":
    asyncio.run(seed())
