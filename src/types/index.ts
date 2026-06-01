export interface Character {
  id: string
  word: string        // 字词（可能是单字或词语）
  pinyin: string      // 拼音
  grade: number       // 年级 7=初一 8=初二 9=初三
  semester: 1 | 2    // 学期
  type: 'char' | 'word' | 'idiom'  // 单字 / 词语 / 成语
}

export interface UserProgress {
  wordId: string
  status: 'new' | 'learning' | 'mastered'
  wrongCount: number
  lastReviewed: string | null
  nextReview: string | null
  // SM-2 fields
  easeFactor: number
  interval: number
  repetitions: number
}

export interface GradeMeta {
  grade: number
  semester: 1 | 2
  label: string      // e.g. "七年级上册"
  total: number
}
