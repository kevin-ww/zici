# Legacy Flask — Migration Reference

This folder contains minimal Flask equivalents of the core Zici API routes. It exists to demonstrate the Flask → FastAPI migration, not to run in production.

## Route Mapping

| Flask (this folder) | FastAPI (`app/routers/`) | Key differences |
|---|---|---|
| `GET /grades` | `GET /api/grades` | Identical shape; FastAPI validates response with `response_model` |
| `GET /words` | `GET /api/words` | Flask returns JSON from files; FastAPI queries Supabase via AsyncSession |
| `GET /words/<word_id>` | `GET /api/words/{word_id}` | FastAPI raises typed `HTTPException(404)` |
| `GET /progress` | `GET /api/progress` | Flask uses in-process dict; FastAPI uses `user_progress` table scoped to JWT user |
| `PUT /progress/<word_id>` | `PUT /api/progress/{word_id}` | FastAPI validates body with Pydantic schema |
| `GET /review/due` | `GET /api/review/due` | FastAPI runs SRS query against DB; Flask filters in-process dict |
| `POST /review/answer` | `POST /api/review/answer` | Same SRS algorithm; FastAPI persists to DB and logs `review_events` |

## Structural Differences

| Concern | Flask | FastAPI |
|---|---|---|
| Route definition | `@blueprint.get(...)` decorator | `@router.get(...)` with `APIRouter` |
| Request handling | `request.args`, `request.get_json()` | Typed function parameters, Pydantic request bodies |
| Response | `jsonify(data)` | Return Python object; FastAPI serialises via `response_model` |
| Async | Synchronous (`def`) | Async (`async def`) throughout |
| Database | No DB (in-process dict) | SQLModel `AsyncSession` → Supabase Postgres |
| Auth | None | JWT bearer token via `Depends(get_current_user)` |
| Validation | Manual | Automatic via Pydantic/SQLModel schemas |
| Docs | None | Auto-generated Swagger UI at `/docs` |

## SRS Algorithm Parity

The `_apply_srs` function in `blueprints/review.py` is the direct Python equivalent of `markWord` in the frontend's `src/lib/storage.ts`. The FastAPI version lives in `app/services/srs.py`. The test suite in `tests/test_parity.py` asserts both produce identical output for the same inputs.
