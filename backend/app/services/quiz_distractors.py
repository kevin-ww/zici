import json
import unicodedata
from datetime import datetime
from collections.abc import Sequence
from types import SimpleNamespace

from openai import AsyncOpenAI
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models.quiz import QuizPinyinDistractorSet
from app.models.word import Word

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"
DISTRACTOR_VERSION = 1
MAX_RULE_CANDIDATES = 12

_INITIALS = [
    "zh", "ch", "sh",
    "b", "p", "m", "f", "d", "t", "n", "l",
    "g", "k", "h", "j", "q", "x", "r", "z", "c", "s",
    "y", "w",
]

_SIMILAR_INITIAL_GROUPS = [
    {"z", "c", "s", "zh", "ch", "sh"},
    {"j", "q", "x"},
    {"n", "l"},
    {"h", "f"},
    {"y", "w"},
]

_SIMILAR_FINAL_GROUPS = [
    {"an", "ang"},
    {"en", "eng"},
    {"in", "ing"},
    {"ian", "iang"},
    {"uan", "uang"},
    {"ou", "uo"},
    {"ie", "ei"},
    {"ui", "iu"},
    {"ao", "iao"},
]


def syllable_count(pinyin: str) -> int:
    parts = [part for part in pinyin.strip().split() if part]
    return len(parts) if parts else 1


def _normalize_pinyin(pinyin: str) -> str:
    text = pinyin.lower().strip()
    for ch in ("ü", "ǖ", "ǘ", "ǚ", "ǜ"):
        text = text.replace(ch, "v")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("'", "").replace("·", "").replace("-", " ")
    return " ".join(part for part in text.split() if part)


def _split_syllable(syllable: str) -> tuple[str, str]:
    for initial in _INITIALS:
        if syllable.startswith(initial):
            return initial, syllable[len(initial):]
    if syllable.startswith("v"):
        return "", syllable
    return "", syllable


def _initial_score(left: str, right: str) -> int:
    if left == right:
        return 5 if left else 3
    for group in _SIMILAR_INITIAL_GROUPS:
        if left in group and right in group:
            return 3
    return 0


def _final_score(left: str, right: str) -> int:
    if left == right:
        return 5
    for group in _SIMILAR_FINAL_GROUPS:
        if left in group and right in group:
            return 3
    if left[:1] == right[:1]:
        return 1
    return 0


def score_pinyin_similarity(target: str, candidate: str) -> int:
    target_parts = _normalize_pinyin(target).split()
    candidate_parts = _normalize_pinyin(candidate).split()
    if len(target_parts) != len(candidate_parts):
        return -1

    score = 0
    for left, right in zip(target_parts, candidate_parts):
        left_initial, left_final = _split_syllable(left)
        right_initial, right_final = _split_syllable(right)
        score += _initial_score(left_initial, right_initial)
        score += _final_score(left_final, right_final)

        if left_initial[:1] == right_initial[:1] and left_initial and right_initial:
            score += 1
        if left_final[:1] == right_final[:1] and left_final and right_final:
            score += 1

    return score


def build_rule_candidates(target: str, all_pinyins: Sequence[str]) -> list[str]:
    target_norm = _normalize_pinyin(target)
    target_count = syllable_count(target)

    scored = []
    seen: set[str] = set()
    for candidate in all_pinyins:
        candidate_norm = _normalize_pinyin(candidate)
        if candidate_norm == target_norm or candidate_norm in seen:
            continue
        seen.add(candidate_norm)
        if syllable_count(candidate) != target_count:
            continue
        score = score_pinyin_similarity(target, candidate)
        if score < 0:
            continue
        scored.append((score, candidate))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [candidate for _, candidate in scored]


def _validate_distractors(target: str, candidates: Sequence[str], selected: Sequence[str]) -> list[str]:
    target_norm = _normalize_pinyin(target)
    valid = []
    seen: set[str] = set()
    allowed = {_normalize_pinyin(candidate) for candidate in candidates}

    for candidate in selected:
        candidate_norm = _normalize_pinyin(candidate)
        if candidate_norm == target_norm:
            continue
        if candidate_norm not in allowed:
            continue
        if candidate_norm in seen:
            continue
        if syllable_count(candidate) != syllable_count(target):
            continue
        seen.add(candidate_norm)
        valid.append(candidate)
        if len(valid) == 3:
            break

    return valid


async def rank_distractors_with_ai(target_word: str, target_pinyin: str, candidates: Sequence[str]) -> list[str] | None:
    if not settings.quiz_ai_enabled or not settings.deepseek_api_key or len(candidates) < 3:
        return None

    client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=DEEPSEEK_BASE_URL)
    prompt = (
        "You are helping create a Mandarin pinyin multiple-choice quiz.\n"
        f"Correct word: {target_word}\n"
        f"Correct pinyin: {target_pinyin}\n"
        "Choose exactly 3 wrong pinyin options from the candidate list below.\n"
        "Rules:\n"
        "- Only choose from the provided candidates.\n"
        "- Prefer options that are genuinely hard to distinguish from the correct pinyin.\n"
        "- Do not choose the correct pinyin.\n"
        "- Return raw JSON only in this format: {\"distractors\": [\"...\", \"...\", \"...\"]}\n\n"
        "Candidates:\n"
        + "\n".join(f"- {candidate}" for candidate in candidates)
    )

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You rank Mandarin pinyin distractors."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None
    distractors = data.get("distractors")
    if not isinstance(distractors, list):
        return None
    validated = _validate_distractors(target_pinyin, candidates, distractors)
    return validated if len(validated) == 3 else None


async def get_or_create_distractor_set(
    session: AsyncSession,
    word: Word,
    all_words: Sequence[Word],
) -> QuizPinyinDistractorSet | SimpleNamespace:
    all_pinyins = [item.pinyin for item in all_words]
    rule_candidates = build_rule_candidates(word.pinyin, all_pinyins)
    if len(rule_candidates) < 3:
        raise ValueError(f"Not enough distractors for {word.word}")

    ai_candidates = rule_candidates[:MAX_RULE_CANDIDATES]
    ai_selected = await rank_distractors_with_ai(word.word, word.pinyin, ai_candidates)
    distractors = ai_selected or rule_candidates[:3]
    distractors = _validate_distractors(word.pinyin, rule_candidates, distractors)
    if len(distractors) < 3:
        distractors = rule_candidates[:3]

    if len(distractors) < 3:
        raise ValueError(f"Not enough valid distractors for {word.word}")

    score = 0.0
    for item in distractors:
        score += score_pinyin_similarity(word.pinyin, item)
    difficulty_score = round(score / len(distractors), 2)
    source = "rules+ai" if ai_selected else "rules"

    try:
        existing = await session.get(QuizPinyinDistractorSet, word.id)
        if existing and existing.generation_version == DISTRACTOR_VERSION:
            return existing

        if existing:
            existing.correct_pinyin = word.pinyin
            existing.distractors_json = distractors
            existing.difficulty_score = difficulty_score
            existing.generation_version = DISTRACTOR_VERSION
            existing.source = source
            existing.updated_at = datetime.utcnow()
            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            return existing

        row = QuizPinyinDistractorSet(
            word_id=word.id,
            correct_pinyin=word.pinyin,
            distractors_json=distractors,
            difficulty_score=difficulty_score,
            generation_version=DISTRACTOR_VERSION,
            source=source,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row
    except SQLAlchemyError:
        await session.rollback()
        return SimpleNamespace(
            word_id=word.id,
            correct_pinyin=word.pinyin,
            distractors_json=distractors,
            difficulty_score=difficulty_score,
            generation_version=DISTRACTOR_VERSION,
            source=source,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
