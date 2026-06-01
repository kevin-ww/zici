import type { Character, GradeMeta } from '@/types'
import { apiGetGrades, apiGetWords } from './api'

export async function getGradeIndex(): Promise<GradeMeta[]> {
  return apiGetGrades()
}

export async function getWords(grade: number, semester: 1 | 2): Promise<Character[]> {
  return apiGetWords(grade, semester)
}

export async function getAllWords(): Promise<Character[]> {
  return apiGetWords()
}

export function gradeLabel(grade: number, semester: 1 | 2): string {
  const names = ['一', '二', '三', '四', '五', '六', '七', '八', '九']
  return `${names[grade - 1]}年级${semester === 1 ? '上' : '下'}册`
}
