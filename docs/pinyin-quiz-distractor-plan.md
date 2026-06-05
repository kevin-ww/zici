# Pinyin Quiz Distractor Plan

## Problem

The current quiz generator picks three random pinyin distractors from the full word bank. That keeps the quiz valid, but the wrong answers are often too easy or too unrelated.

Example: for `招徕 (zhāo lái)`, a strong quiz should offer answers that are genuinely confusing to a learner, not just random pinyin strings.

## Goal

Generate multiple-choice pinyin quizzes where each wrong answer is:

- the same syllable count as the correct answer
- phonetically similar enough to be plausible
- not obviously unrelated
- reusable across sessions so the quiz does not need to be recomputed every time

## Proposed Approach

Use a hybrid pipeline:

1. deterministic phonetic candidate generation
2. AI ranking or filtering of those candidates
3. database storage of the validated quiz distractors
4. runtime fallback to rules if cached data is missing

The key decision is that AI should not invent distractors from scratch. It should rank or refine candidates produced by rules.

## Why Hybrid

Pure rules are consistent but sometimes too weak.
Pure AI is flexible but can be unpredictable and hard to validate.

Combining both gives us:

- predictable output shape
- better distractor quality
- easier testing
- lower runtime latency after caching

## Data Model

Add a table for precomputed quiz choices, for example:

```text
quiz_pinyin_options
  id
  word_id
  correct_pinyin
  distractors_json
  difficulty_score
  generation_version
  source
  created_at
  updated_at
```

Suggested fields:

- `word_id`: the target word
- `correct_pinyin`: stored for validation and rebuilds
- `distractors_json`: ordered list of distractors
- `difficulty_score`: optional ranking metric
- `generation_version`: lets us regenerate later without ambiguity
- `source`: `rules`, `ai`, or `rules+ai`

## Generation Pipeline

### Step 1: Build candidate pool

For each word:

- match syllable count first
- prefer candidates with similar initials and finals
- include known confusion groups such as:
  - `zh / z / ch / c / sh / s`
  - `j / q / x`
  - `n / l`
  - `h / f`
  - similar final patterns such as `an / ang`, `en / eng`, `in / ing`

### Step 2: Rank candidates

Pass the correct pinyin and candidate set to AI.

The AI task is:

- score which distractors are most confusing
- reject options that are too easy or too distant
- keep the final set to exactly three distractors

### Step 3: Store result

Persist the selected distractors in the database so the frontend can read them directly.

### Step 4: Reuse at runtime

Quiz generation should first look for cached distractors.
If cached data exists, use it immediately.
If not, generate on demand and optionally backfill the cache asynchronously.

## Runtime Behavior

At quiz time:

1. load the target word
2. fetch cached distractors if available
3. otherwise build them with the rules+AI pipeline
4. return the correct answer plus three wrong options in randomized order

## Validation Rules

Every generated quiz question must satisfy:

- correct answer appears exactly once
- exactly four options total
- all options share the same syllable count when possible
- distractors are unique
- distractors are not identical to the correct answer
- distractors pass basic phonetic sanity checks

## Fallback Strategy

If AI generation fails:

- use the rule-based candidate pool only
- store the fallback result with `source = rules`
- keep the quiz available instead of blocking the user

## Testing Plan

Add tests for:

- syllable count matching
- no duplicate options
- correct answer included exactly once
- cached distractor reuse
- fallback behavior when AI is unavailable
- difficulty ranking for a sample of known tricky words

## Rollout Plan

### Phase 1

Implement the new table and backfill a small subset of words.

### Phase 2

Switch quiz generation to use cached distractors when present.

### Phase 3

Expand generation to the full word bank and monitor quality.

### Phase 4

Tune the AI ranking prompt and the phonetic candidate rules based on observed quiz quality.

## Risks

- AI may still pick poor distractors if the candidate pool is weak
- some words will have too few good phonetic neighbors
- cached data needs versioning so improved rules can replace old output cleanly
- generation latency should not block the quiz UI

## Recommendation

Do not let AI directly invent the final quiz answers.
Use rules to generate a valid candidate set, then let AI rank or narrow that set, and finally save the result for reuse.

This gives better quiz quality without losing predictability.
