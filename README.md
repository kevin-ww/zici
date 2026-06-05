# Zici — Junior High Chinese Vocabulary Learning Tool

An intelligent Chinese vocabulary learning tool designed for junior high school students (grades 6–9). The app helps students systematically build and retain the vocabulary required by the Chinese language curriculum, with spaced repetition, pinyin quizzes, AI-powered word explanations, and per-student progress tracking.

## Background

Junior high students in China face a significant vocabulary load across grades 6–9 — hundreds of characters, words, and idioms that appear in exams and compositions. Rote memorisation is ineffective at scale. This app applies spaced repetition (SM-2) to surface the right words at the right time, and uses AI to provide contextual explanations that go beyond a dictionary definition.


## Features

- **Structured word catalog** — 1,083 characters, words, and idioms across grades 7–9, plus targeted common-mistake sets (易错词语 / 易错成语)
- **Spaced repetition review** — server-side SM-2 algorithm with full review history
- **Pinyin quiz** — multiple-choice questions; correct answers withheld until submission to prevent guessing
- **Learning statistics** — mastery rate per grade, per semester, and overall
- **AI word explanation** — DeepSeek-powered explanations with pinyin, usage context, and example sentences; supports beginner / intermediate / advanced levels in English or Chinese
- **Per-student accounts** — JWT authentication, progress isolated per user

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript |
| Backend | FastAPI (async/await), Python 3.11 |
| ORM | SQLModel + asyncpg |
| Database | Supabase PostgreSQL |
| Auth | JWT bearer tokens, bcrypt |
| AI | DeepSeek via OpenAI-compatible SDK |
| Tests | pytest + pytest-asyncio (57 tests) |
| Package manager | uv (backend), npm (frontend) |

## Project Structure

```
zici/
  src/                          # Next.js frontend
    app/
      login/page.tsx            # Login / register
      page.tsx                  # Home — grade index with mastery progress
      review/page.tsx           # Spaced repetition review session
      quiz/page.tsx             # Pinyin multiple-choice quiz
      stats/page.tsx            # Learning statistics dashboard
      grade/[id]/page.tsx       # Per-grade word list with status filter
    components/
      AuthGate.tsx              # Redirects unauthenticated users to /login
      UserMenu.tsx              # Avatar dropdown with profile and logout
      FlashCard.tsx             # Review flash card component
    lib/
      api.ts                    # Typed fetch client for all backend endpoints
      auth.tsx                  # AuthContext + JWT token management
      data.ts                   # Word data functions (→ GET /api/words)
      storage.ts                # Progress functions (→ backend API)
  backend/
    app/
      routers/                  # FastAPI routers: auth, words, progress, review, stats, quiz, chat
      services/                 # Business logic: srs.py, auth.py, words.py, quiz.py, stats.py, chat.py
      models/                   # SQLModel table models: user, word, user_progress, review_events, quiz
      schemas/                  # Request/response shapes separate from DB models
      core/                     # Config, security, JWT dependency
      data/                     # Seeded JSON word files (9 files, 1,083 entries)
    tests/                      # 57 tests: SRS unit, parity, API, auth, stats, quiz, chat
    legacy_flask/               # Flask blueprint equivalents (migration reference)
    scripts/
      seed_demo.py              # Creates all tables, seeds words, creates demo account
```

## Quick Start

### Prerequisites

Node.js 18+, Python 3.11+, [uv](https://docs.astral.sh/uv/), Docker

### One-command local demo

```bash
./dev.sh start
```

This starts the local Supabase stack, FastAPI backend, and Next.js frontend.

```text
Frontend:     http://localhost:3000
FastAPI docs: http://localhost:8000/docs
Health check: http://localhost:8000/health
Demo user:    demo@zici.app / demo1234
```

Service-level control is also available:

```bash
./dev.sh frontend start|stop|restart|status
./dev.sh backend start|stop|restart|status
./dev.sh db start|stop|restart|status
./dev.sh status
```

Log files:

- Frontend: `/tmp/zici-frontend.log`
- Backend: `/tmp/zici-backend.log`
- Database: `/tmp/zici-supabase.log`

### 1. Backend

```bash
cd backend

# Install dependencies
uv sync

# Start local Supabase (requires Docker)
DOCKER_HOST="unix:///var/run/docker.sock" supabase start

# Configure environment
cp .env.example .env
# DATABASE_URL is pre-filled for local Supabase — only DEEPSEEK_API_KEY and JWT_SECRET_KEY need changing

# Seed database (creates tables + demo account)
uv run python scripts/seed_demo.py

# Start API server
uv run uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Frontend

```bash
# From project root
npm install
npm run dev
```

App available at: http://localhost:3000

### Demo Account

```
Email:    demo@zici.app
Password: demo1234
```

## Environment Variables

```env
# Local Supabase (default after supabase start)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres

# Remote Supabase — use transaction pooler (port 6543)
# DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-1-[region].pooler.supabase.com:6543/postgres

JWT_SECRET_KEY=<run: openssl rand -hex 32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
DEEPSEEK_API_KEY=<your DeepSeek key>
```

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

See [docs/api-examples.md](./docs/api-examples.md) for copy-paste curl examples covering registration, login, review, quiz, stats, and AI explanation.

## Architecture

```mermaid
flowchart LR
  User[Student browser] --> Frontend[Next.js 15 + React 19]
  Frontend --> API[FastAPI backend]
  API --> Auth[JWT auth dependencies]
  API --> Services[Service layer]
  Services --> SRS[SRS review scheduler]
  Services --> Quiz[Quiz generator]
  Services --> Chat[AI explanation service]
  API --> DB[(Supabase PostgreSQL)]
  Chat --> AI[DeepSeek / OpenAI-compatible API]
```

The backend keeps HTTP concerns in routers, request/response contracts in schemas, persistence in SQLModel models, and business rules in services. See [docs/architecture.md](./docs/architecture.md) for more detail.

## Spaced Repetition Algorithm (SM-2)

The review scheduler surfaces words at increasing intervals as the student demonstrates recall:

- **Correct answer**: repetitions +1 → interval: 1 day → 6 days → `round(interval × ease_factor)` → marked mastered at repetitions ≥ 3; ease factor increases by 0.1 (floor 1.3)
- **Wrong answer**: repetitions and interval reset to 1, ease factor decreases by 0.2 (floor 1.3), status reverts to learning
- All review dates stored and compared in UTC

`tests/test_parity.py` verifies the Python implementation produces identical output to the original TypeScript algorithm — the regression prevention strategy used when migrating client-side logic to the server.

## Flask → FastAPI Migration Reference

`legacy_flask/` contains minimal Flask blueprint equivalents of the three core API routes (words, progress, review). The same functionality is re-implemented in `backend/app/` using FastAPI, showing the structural migration pattern:

| Concern | Flask (`legacy_flask/`) | FastAPI (`app/`) |
|---|---|---|
| Route grouping | `Blueprint` | `APIRouter` |
| Route definition | `@bp.get("/words")` | `@router.get("/words")` |
| Request handling | `request.args`, `request.get_json()` | Typed function parameters + Pydantic |
| Response | `jsonify(data)` | Python object serialised via `response_model` |
| I/O model | Synchronous `def` | Async `async def` throughout |
| Database | In-process dict | SQLModel `AsyncSession` → Supabase Postgres |
| Auth | None | JWT bearer token via `Depends(get_current_user)` |
| API docs | None | Auto-generated Swagger UI at `/docs` |

## Testing

```bash
cd backend && uv run pytest tests/ -v
```

Expected result: all backend tests pass locally without a Supabase connection. The test suite uses SQLite in-memory fixtures and currently covers 57 tests:

| File | Coverage |
|---|---|
| `test_srs.py` | SM-2 algorithm unit tests including boundary conditions |
| `test_parity.py` | Python vs original TypeScript algorithm parity |
| `test_auth.py` | Registration, login, JWT validation, user scoping |
| `test_words.py` | Word catalog endpoints including yicuo entries |
| `test_review.py` | Review endpoints, due queue, per-user isolation |
| `test_stats.py` | Stats aggregation by grade and overview |
| `test_quiz.py` | Quiz generation, answer scoring, attempt linking |
| `test_chat.py` | DeepSeek integration with mocked responses |

Fast smoke checks before sharing the repo:

```bash
cd backend && uv run pytest tests/test_parity.py -v
cd backend && uv run pytest tests/test_auth.py tests/test_review.py -v
```

The parity suite is the key migration proof: it verifies the Python FastAPI SRS implementation preserves the original TypeScript review behavior.

## Deployment

| Component | Service |
|---|---|
| Frontend | Vercel |
| Backend | Render / Railway / Fly.io |
| Database | Supabase Postgres (Tokyo region) |

Production notes:
- Supabase transaction pooler (port 6543) requires `statement_cache_size=0` in asyncpg connect args
- Set `BACKEND_CORS_ORIGINS` to your deployed Vercel URL — never a wildcard
- `DEEPSEEK_API_KEY` must remain server-side only

## License

This project's source code is licensed under the MIT License. See [LICENSE](./LICENSE).

Vocabulary datasets may have separate source terms. Please verify data rights before commercial reuse.
