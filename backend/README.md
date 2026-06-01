# Zici Backend

FastAPI backend for the Zici junior high Chinese vocabulary learning tool. Serves the word catalog, manages per-student spaced repetition progress, and provides AI-powered word explanations.

Built as a portfolio demonstration of Flask → FastAPI migration skills for the Mandarin Blueprint Backend Developer role.

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (async/await) |
| ORM | SQLModel + asyncpg |
| Database | Supabase PostgreSQL |
| Auth | JWT bearer tokens (python-jose + bcrypt) |
| AI | DeepSeek via OpenAI-compatible SDK |
| Tests | pytest + pytest-asyncio (SQLite in-memory) |
| Package manager | uv |

## Local Development

**Requirements**: Python 3.11+, uv, Docker

```bash
# 1. Install dependencies
uv sync

# 2. Start local Supabase
DOCKER_HOST="unix:///var/run/docker.sock" supabase start

# 3. Configure environment
cp .env.example .env
# DATABASE_URL is pre-filled — set DEEPSEEK_API_KEY and JWT_SECRET_KEY

# 4. Run Alembic migrations
uv run alembic upgrade head

# 5. Seed demo data
uv run python scripts/seed_demo.py

# 6. Start the API server
uv run uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

Demo account: `demo@zici.app` / `demo1234`

## API Overview

### Public

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/grades` | Grade and semester index |
| GET | `/api/words` | Word catalog (filterable by grade/semester) |
| GET | `/api/words/{id}` | Single word |
| POST | `/api/auth/register` | Register new student account |
| POST | `/api/auth/login` | Login, returns JWT bearer token |
| GET | `/api/auth/me` | Current user profile |

### Protected (Bearer token required)

| Method | Path | Description |
|---|---|---|
| GET | `/api/progress` | All learning progress for current user |
| GET | `/api/progress/{word_id}` | Progress for a single word |
| GET | `/api/review/due` | Words due for review today |
| POST | `/api/review/answer` | Submit review answer, applies SM-2 |
| GET | `/api/stats/overview` | Overall mastery statistics |
| GET | `/api/stats/by-grade` | Mastery breakdown by grade and semester |
| POST | `/api/quiz` | Generate a pinyin quiz (answers withheld) |
| POST | `/api/quiz/answer` | Submit quiz answers, returns score and correct answers |
| POST | `/api/chat/explain-word` | AI explanation with example sentence |

## Database Migrations

Managed with Alembic. Migration files live in `alembic/versions/`.

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Roll back one migration
uv run alembic downgrade -1

# Check current revision
uv run alembic current

# Show migration history
uv run alembic history --verbose

# Generate a new migration from model changes
uv run alembic revision --autogenerate -m "describe the change"
```

### Migration history

| Revision | Description |
|---|---|
| `2903595ebba4` | Create initial tables (users, words, user_progress, review_events, quiz_attempts, quiz_answers) |
| `7e7ac2050152` | Add `display_language` preference column to users |

## Migration Story: Flask → FastAPI

This project demonstrates the structural migration pattern used when converting a Flask application to FastAPI. `legacy_flask/` contains minimal Flask blueprint equivalents for words, progress, and review. The same logic is implemented in `app/` using async FastAPI patterns.

### Structural Mapping

| Concern | Flask (`legacy_flask/`) | FastAPI (`app/`) |
|---|---|---|
| Route grouping | `Blueprint` | `APIRouter` |
| Route definition | `@bp.get("/words")` | `@router.get("/words")` |
| Request handling | `request.args`, `request.get_json()` | Typed function parameters + Pydantic |
| Response | `jsonify(data)` | Python object serialised via `response_model` |
| I/O model | Synchronous `def` | Async `async def` throughout |
| Database | In-process dict | SQLModel `AsyncSession` → Supabase Postgres |
| Auth | None | JWT bearer token via `Depends(get_current_user)` |
| Validation | Manual | Automatic via Pydantic/SQLModel schemas |
| API docs | None | Auto-generated Swagger UI at `/docs` |

### SRS Algorithm Parity

`legacy_flask/blueprints/review.py` contains `_apply_srs()` — the direct Python equivalent of the original TypeScript `markWord()` in `src/lib/storage.ts`. The FastAPI version lives in `app/services/srs.py`. `tests/test_parity.py` asserts both produce identical output for the same inputs — this is the regression prevention strategy for the migration.

## Spaced Repetition Algorithm (SM-2)

Students review words at intervals determined by their recall performance:

- **Correct answer**: repetitions +1, ease factor +0.1 (floor 1.3), interval: 1 day → 6 days → `round(interval × ease_factor)`, mastered at repetitions ≥ 3
- **Wrong answer**: repetitions and interval reset to 1, ease factor −0.2 (floor 1.3), status → learning
- All review dates stored and compared in UTC, matching the original client-side behaviour

## Testing

```bash
uv run pytest tests/ -v
```

57 tests using SQLite in-memory — no Supabase connection required.

| File | Coverage |
|---|---|
| `test_srs.py` | SM-2 unit tests including boundary conditions (rep==2 learning, rep==3 mastered) |
| `test_parity.py` | Python vs original TypeScript algorithm parity |
| `test_auth.py` | Registration, login, JWT validation, user scoping |
| `test_words.py` | Word catalog endpoints |
| `test_review.py` | Review endpoints, due queue, per-user isolation |
| `test_stats.py` | Stats aggregation by grade and overview |
| `test_quiz.py` | Quiz generation, answer scoring, attempt linking |
| `test_chat.py` | DeepSeek integration (mocked) |

## Deployment

| Component | Service |
|---|---|
| Frontend | Vercel |
| Backend | Render / Railway / Fly.io |
| Database | Supabase Postgres (Tokyo region) |

### Environment Variables

```env
# Local Supabase
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres

# Remote Supabase (transaction pooler, port 6543)
# DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-1-[region].pooler.supabase.com:6543/postgres

JWT_SECRET_KEY=<run: openssl rand -hex 32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BACKEND_CORS_ORIGINS=["https://your-frontend.vercel.app"]
DEEPSEEK_API_KEY=<your DeepSeek key>
```

### Running with Gunicorn (production)

```bash
# Install gunicorn (already in pyproject.toml)
uv sync

# Start with Uvicorn workers (required for FastAPI / ASGI)
gunicorn app.main:app -c gunicorn.conf.py

# Or override workers and port via env vars
WEB_CONCURRENCY=4 PORT=8000 gunicorn app.main:app -c gunicorn.conf.py
```

`gunicorn.conf.py` sets:
- `worker_class = "uvicorn.workers.UvicornWorker"` — ASGI-compatible worker for FastAPI
- `workers = 2 × CPU_COUNT + 1` (overridden by `WEB_CONCURRENCY` env var)
- `bind = 0.0.0.0:$PORT` — reads `PORT` from environment (set automatically on Render/Railway)
- `timeout = 30`, `graceful_timeout = 10` — safe for long DB queries

### Production Notes

- Supabase transaction pooler (port 6543) requires `statement_cache_size=0` in asyncpg connect args
- Set `BACKEND_CORS_ORIGINS` to your deployed Vercel URL — never a wildcard
- JWT stored as bearer token; `httpOnly` cookie upgrade is documented as a next step
- `DEEPSEEK_API_KEY` must remain server-side only
