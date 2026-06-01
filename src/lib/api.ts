import type { Character, GradeMeta, UserProgress } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

// ---- token store (in-memory, survives re-renders via module scope) ----
let _token: string | null = null

export function setToken(t: string | null) { _token = t }
export function getToken(): string | null { return _token }

function authHeaders(): Record<string, string> {
  return _token ? { Authorization: `Bearer ${_token}` } : {}
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `API error ${res.status}`)
  }
  return res.json()
}

// ---- Auth ----

export async function apiRegister(email: string, password: string, displayName?: string) {
  return apiFetch<{ id: string; email: string; display_name: string | null }>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
  })
}

export async function apiLogin(email: string, password: string): Promise<string> {
  const data = await apiFetch<{ access_token: string }>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  return data.access_token
}

export async function apiMe() {
  return apiFetch<{ id: string; email: string; display_name: string | null }>('/api/auth/me')
}

// ---- Words ----

export async function apiGetGrades(): Promise<GradeMeta[]> {
  return apiFetch('/api/grades')
}

export async function apiGetWords(grade?: number, semester?: number): Promise<Character[]> {
  const params = new URLSearchParams()
  if (grade !== undefined) params.set('grade', String(grade))
  if (semester !== undefined) params.set('semester', String(semester))
  const qs = params.toString()
  return apiFetch(`/api/words${qs ? '?' + qs : ''}`)
}

// ---- Progress (snake_case → camelCase) ----

interface ApiProgress {
  word_id: string
  status: 'new' | 'learning' | 'mastered'
  wrong_count: number
  last_reviewed: string | null
  next_review: string | null
  ease_factor: number
  interval: number
  repetitions: number
}

function toProgress(p: ApiProgress): UserProgress {
  return {
    wordId: p.word_id,
    status: p.status,
    wrongCount: p.wrong_count,
    lastReviewed: p.last_reviewed,
    nextReview: p.next_review,
    easeFactor: p.ease_factor,
    interval: p.interval,
    repetitions: p.repetitions,
  }
}

export async function apiGetAllProgress(): Promise<UserProgress[]> {
  const list = await apiFetch<ApiProgress[]>('/api/progress')
  return list.map(toProgress)
}

export async function apiGetProgress(wordId: string): Promise<UserProgress | null> {
  try {
    const p = await apiFetch<ApiProgress>(`/api/progress/${wordId}`)
    return toProgress(p)
  } catch {
    return null
  }
}

export async function apiMarkWord(wordId: string, correct: boolean): Promise<UserProgress> {
  const p = await apiFetch<ApiProgress>('/api/review/answer', {
    method: 'POST',
    body: JSON.stringify({ word_id: wordId, correct }),
  })
  return toProgress(p)
}

export async function apiGetDue(limit = 30): Promise<(Character & { progress: UserProgress })[]> {
  const items = await apiFetch<(Character & { progress: ApiProgress })[]>(`/api/review/due?limit=${limit}`)
  return items.map(item => ({ ...item, progress: toProgress(item.progress) }))
}

// ---- Stats ----

export interface StatsOverview {
  total: number
  mastered: number
  learning: number
  new_count: number
  mastered_percent: number
}

export interface StatsByGrade {
  grade: number
  semester: number
  total: number
  mastered: number
  learning: number
  new_count: number
  mastered_percent: number
}

export async function apiGetStatsOverview(): Promise<StatsOverview> {
  return apiFetch('/api/stats/overview')
}

export async function apiGetStatsByGrade(): Promise<StatsByGrade[]> {
  return apiFetch('/api/stats/by-grade')
}

// ---- Quiz ----

export interface QuizQuestion {
  word_id: string
  word: string
  options: string[]
}

export interface QuizResponse {
  quiz_attempt_id: string
  questions: QuizQuestion[]
}

export interface QuizResult {
  word_id: string
  correct_answer: string
  selected_answer: string
  is_correct: boolean
}

export interface QuizAnswerResponse {
  quiz_attempt_id: string
  score: number
  total: number
  results: QuizResult[]
}

export async function apiCreateQuiz(limit = 10, grade?: number, semester?: number): Promise<QuizResponse> {
  return apiFetch('/api/quiz', {
    method: 'POST',
    body: JSON.stringify({ limit, grade, semester }),
  })
}

export async function apiSubmitQuiz(
  quizAttemptId: string,
  answers: { word_id: string; selected_answer: string }[]
): Promise<QuizAnswerResponse> {
  return apiFetch('/api/quiz/answer', {
    method: 'POST',
    body: JSON.stringify({ quiz_attempt_id: quizAttemptId, answers }),
  })
}

// ---- Chat ----

export interface ExampleSentence {
  sentence: string
  translation: string
  is_classical: boolean
}

export interface ExplainWordResponse {
  word: string
  pinyin: string
  explanation_zh: string
  explanation: string
  examples: ExampleSentence[]
}

export async function apiExplainWord(
  word: string,
  level: 'beginner' | 'intermediate' | 'advanced' = 'intermediate',
  language: 'en' | 'zh' = 'en',
): Promise<ExplainWordResponse> {
  return apiFetch('/api/chat/explain-word', {
    method: 'POST',
    body: JSON.stringify({ word, level, language }),
  })
}
