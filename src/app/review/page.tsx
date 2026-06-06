'use client'

import { useEffect, useMemo, useState } from 'react'
import type { Character } from '@/types'
import { apiExplainWord, apiGetDue, apiMarkWord, type ExplainWordResponse } from '@/lib/api'
import FlashCard from '@/components/FlashCard'

export default function ReviewPage() {
  const [queue, setQueue] = useState<Character[]>([])
  const [current, setCurrent] = useState(0)
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(true)
  const [reviewMode, setReviewMode] = useState<'pinyin' | 'meaning'>('pinyin')
  const [meaning, setMeaning] = useState<ExplainWordResponse | null>(null)
  const [meaningLoading, setMeaningLoading] = useState(false)
  const [meaningError, setMeaningError] = useState('')

  useEffect(() => {
    apiGetDue(30)
      .then(items => setQueue(items.map(({ progress: _p, ...w }) => w as Character)))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const word = useMemo(() => queue[current] ?? null, [queue, current])

  useEffect(() => {
    setMeaning(null)
    setMeaningError('')
    setMeaningLoading(false)
  }, [reviewMode, word])

  async function handleRevealMeaning() {
    if (!word || reviewMode !== 'meaning') return false
    setMeaningError('')
    setMeaningLoading(true)
    try {
      const result = await apiExplainWord(word.word, 'intermediate', 'en')
      setMeaning(result)
      return true
    } catch (e) {
      setMeaningError(e instanceof Error ? e.message : 'AI unavailable')
      return false
    } finally {
      setMeaningLoading(false)
    }
  }

  async function handleAnswer(correct: boolean) {
    const word = queue[current]
    await apiMarkWord(word.id, correct)
    if (current + 1 >= queue.length) {
      setDone(true)
    } else {
      setCurrent(c => c + 1)
    }
  }

  if (loading) return <div style={{ padding: 24, color: 'var(--muted)' }}>加载中...</div>

  if (queue.length === 0) return (
    <div style={{ padding: 24, textAlign: 'center' }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>🎉</div>
      <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>今日复习完成！</div>
      <div style={{ color: 'var(--muted)', fontSize: 14 }}>暂无待复习字词，明天再来吧</div>
    </div>
  )

  if (done) return (
    <div style={{ padding: 24, textAlign: 'center' }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
      <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>本轮复习完成！</div>
      <div style={{ color: 'var(--muted)', fontSize: 14, marginBottom: 24 }}>
        共复习 {queue.length} 个字词
      </div>
      <button onClick={() => { setCurrent(0); setDone(false) }} style={{
        padding: '12px 32px', borderRadius: 12, border: 'none', cursor: 'pointer',
        background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 600,
      }}>再来一遍</button>
    </div>
  )

  const promptLabel = reviewMode === 'meaning' ? '释义' : '拼音'
  const promptText = word.word
  const answerLabel = reviewMode === 'meaning' ? '释义' : '拼音'
  const answerText = reviewMode === 'meaning' ? (meaning?.explanation_zh ?? '') : word.pinyin
  const meaningSource = meaning?.source_text
    ? `${meaning.source_type ? `${meaning.source_type}：` : ''}${meaning.source_text}`
    : meaning?.source_type ?? ''
  const answerSubText = reviewMode === 'meaning'
    ? [meaning?.explanation, meaningSource].filter(Boolean).join('\n')
    : undefined

  return (
    <div style={{ padding: '20px 16px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700 }}>今日复习</h1>
        <span style={{ color: 'var(--muted)', fontSize: 14 }}>{current + 1} / {queue.length}</span>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {([
          { key: 'pinyin', label: '拼音' },
          { key: 'meaning', label: '释义' },
        ] as const).map(item => (
          <button
            key={item.key}
            onClick={() => setReviewMode(item.key)}
            style={{
              padding: '5px 12px',
              borderRadius: 20,
              border: 'none',
              cursor: 'pointer',
              fontSize: 12,
              background: reviewMode === item.key ? 'var(--primary)' : 'var(--border)',
              color: reviewMode === item.key ? '#fff' : 'var(--muted)',
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, marginBottom: 24, overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${((current + 1) / queue.length) * 100}%`,
          background: 'var(--primary)', borderRadius: 3, transition: 'width 0.3s'
        }} />
      </div>

      <FlashCard
        key={`${word.id}-${reviewMode}`}
        word={word}
        mode="review"
        promptLabel={promptLabel}
        promptText={promptText}
        answerLabel={answerLabel}
        answerText={answerText}
        answerSubText={answerSubText}
        revealLabel={reviewMode === 'meaning' ? '查看释义' : '查看拼音'}
        revealLoading={reviewMode === 'meaning' ? meaningLoading : false}
        onReveal={reviewMode === 'meaning' ? handleRevealMeaning : undefined}
        onCorrect={() => handleAnswer(true)}
        onWrong={() => handleAnswer(false)}
      />

      {meaningError && reviewMode === 'meaning' && (
        <div style={{ marginTop: 12, padding: '10px 14px', background: '#fee2e2', borderRadius: 10, fontSize: 13, color: '#dc2626' }}>
          {meaningError}
        </div>
      )}
    </div>
  )
}
