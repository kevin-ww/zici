# API Examples

These examples assume the backend is running at `http://localhost:8000`.

Start the full local stack:

```bash
./dev.sh start
```

Set a base URL:

```bash
API=http://localhost:8000
```

## Health Check

```bash
curl "$API/health"
```

Expected response:

```json
{"status":"ok"}
```

## Register

```bash
curl -X POST "$API/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo2@zici.app",
    "password": "demo1234",
    "display_name": "Demo Student"
  }'
```

## Login

```bash
TOKEN=$(curl -s -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@zici.app",
    "password": "demo1234"
  }' | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
```

Verify the token:

```bash
curl "$API/api/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

## Word Catalog

List grades:

```bash
curl "$API/api/grades"
```

List words for one semester:

```bash
curl "$API/api/words?grade=7&semester=1"
```

Get one word:

```bash
curl "$API/api/words/7-1-001"
```

## Review Flow

Get due words:

```bash
curl "$API/api/review/due?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

Submit a review answer:

```bash
curl -X POST "$API/api/review/answer" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "word_id": "7-1-001",
    "correct": true
  }'
```

The response includes the updated SRS state:

```json
{
  "word_id": "7-1-001",
  "status": "learning",
  "wrong_count": 0,
  "last_reviewed": "2026-06-01",
  "next_review": "2026-06-02",
  "ease_factor": 2.6,
  "interval": 1,
  "repetitions": 1
}
```

## Stats

```bash
curl "$API/api/stats/overview" \
  -H "Authorization: Bearer $TOKEN"
```

```bash
curl "$API/api/stats/by-grade" \
  -H "Authorization: Bearer $TOKEN"
```

## Quiz

Create a quiz. Answers are intentionally withheld until submission.

```bash
QUIZ_ID=$(curl -s -X POST "$API/api/quiz" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 3,
    "grade": 7,
    "semester": 1
  }' | python -c 'import json,sys; print(json.load(sys.stdin)["quiz_attempt_id"])')
```

Submit answers:

```bash
curl -X POST "$API/api/quiz/answer" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"quiz_attempt_id\": \"$QUIZ_ID\",
    \"answers\": [
      {
        \"word_id\": \"7-1-001\",
        \"selected_answer\": \"shi4 li4\"
      }
    ]
  }"
```

## AI Word Explanation

```bash
curl -X POST "$API/api/chat/explain-word" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "矛盾",
    "level": "intermediate",
    "language": "en"
  }'
```

This endpoint calls the AI provider from the backend so the API key never reaches the browser. In tests, the provider is mocked.
