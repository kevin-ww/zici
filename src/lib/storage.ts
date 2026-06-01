import type { UserProgress } from '@/types'
import { apiGetAllProgress, apiGetProgress, apiMarkWord } from './api'

export async function getProgress(wordId: string): Promise<UserProgress | null> {
  return apiGetProgress(wordId)
}

export async function getAllProgress(): Promise<UserProgress[]> {
  return apiGetAllProgress()
}

export function defaultProgress(wordId: string): UserProgress {
  return {
    wordId,
    status: 'new',
    wrongCount: 0,
    lastReviewed: null,
    nextReview: null,
    easeFactor: 2.5,
    interval: 1,
    repetitions: 0,
  }
}

export async function markWord(wordId: string, correct: boolean): Promise<void> {
  await apiMarkWord(wordId, correct)
}
