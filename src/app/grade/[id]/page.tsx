'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import type { Character, UserProgress } from '@/types'
import { getWords } from '@/lib/data'
import { getAllProgress, markWord } from '@/lib/storage'
import { apiExplainWord, type ExplainWordResponse } from '@/lib/api'
import FlashCard from '@/components/FlashCard'

export default function GradePage() {
  const { id } = useParams<{ id: string }>()
  const [grade, semester] = (id ?? '').split('-').map(Number) as [number, 1 | 2]

  const [words, setWords] = useState<Character[]>([])
  const [progress, setProgress] = useState<Record<string, UserProgress>>({})
  const [active, setActive] = useState<Character | null>(null)
  const [filter, setFilter] = useState<'all' | 'new' | 'learning' | 'mastered'>('all')

  // AI explanation state
  const [explanation, setExplanation] = useState<ExplainWordResponse | null>(null)
  const [explaining, setExplaining] = useState(false)
  const [explainError, setExplainError] = useState('')

  useEffect(() => {
    if (!grade) return
    getWords(grade, semester).then(setWords)
    getAllProgress().then(list => {
      const map: Record<string, UserProgress> = {}
      list.forEach(p => { map[p.wordId] = p })
      setProgress(map)
    })
  }, [grade, semester])

  function handleOpen(word: Character) {
    setActive(word)
    setExplanation(null)
    setExplainError('')
  }

  async function handleExplain() {
    if (!active || explaining) return false
    setExplaining(true)
    setExplainError('')
    setExplanation(null)
    try {
      const result = await apiExplainWord(active.word, 'intermediate', 'en')
      setExplanation(result)
      return true
    } catch (e) {
      setExplainError(e instanceof Error ? e.message : 'AI unavailable')
      return false
    } finally {
      setExplaining(false)
    }
  }

  async function handleMark(correct: boolean) {
    if (!active) return
    await markWord(active.id, correct)
    const updated = progress[active.id] ?? { wordId: active.id, status: 'new', wrongCount: 0, lastReviewed: null, nextReview: null, easeFactor: 2.5, interval: 1, repetitions: 0 }
    updated.status = correct ? (updated.repetitions >= 2 ? 'mastered' : 'learning') : 'learning'
    setProgress(prev => ({ ...prev, [active.id]: { ...updated } }))
    setActive(null)
    setExplanation(null)
  }

  const gradeNames: Record<number, string> = { 7: '初一', 8: '初二', 9: '初三' }
  const semLabel = semester === 1 ? '上册' : '下册'
  const title = `${gradeNames[grade] ?? `${grade}年级`}${semLabel}`

  const filtered = words.filter(w => {
    if (filter === 'all') return true
    const s = progress[w.id]?.status ?? 'new'
    return s === filter
  })

  const statusColor: Record<string, string> = {
    mastered: 'var(--mastered)', learning: 'var(--learning)', new: 'var(--new)'
  }

  const typeLabel: Record<string, string> = { char: '字', word: '词', idiom: '成语' }

  return (
    <div style={{ padding: '20px 16px 0' }}>
      <a href="/" style={{ color: 'var(--primary)', fontSize: 14, textDecoration: 'none' }}>← 返回</a>
      <h1 style={{ fontSize: 22, fontWeight: 700, margin: '8px 0 4px' }}>{title}</h1>
      <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 16 }}>共 {words.length} 个字词</p>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {(['all', 'new', 'learning', 'mastered'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '5px 12px', borderRadius: 20, border: 'none', cursor: 'pointer', fontSize: 12,
            background: filter === f ? 'var(--primary)' : 'var(--border)',
            color: filter === f ? '#fff' : 'var(--muted)',
          }}>
            {f === 'all' ? '全部' : f === 'new' ? '未学' : f === 'learning' ? '学习中' : '已掌握'}
          </button>
        ))}
      </div>

      {/* Word grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
        {filtered.map(w => {
          const s = progress[w.id]?.status ?? 'new'
          return (
            <button key={w.id} data-demo-word={w.id} onClick={() => handleOpen(w)} style={{
              background: '#fff', border: `2px solid ${statusColor[s]}`,
              borderRadius: 12, padding: '12px 8px', cursor: 'pointer',
              textAlign: 'center', position: 'relative',
            }}>
              <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>{w.word}</div>
              <div style={{ fontSize: 10, color: 'var(--muted)' }}>{typeLabel[w.type]}</div>
              <div style={{
                position: 'absolute', top: 6, right: 6, width: 8, height: 8,
                borderRadius: '50%', background: statusColor[s]
              }} />
            </button>
          )
        })}
      </div>

      {/* Flash card overlay */}
      {active && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 200, padding: 16,
        }} onClick={() => { setActive(null); setExplanation(null) }}>
          <div onClick={e => e.stopPropagation()} style={{
            width: '100%', maxWidth: 480,
            background: '#fff', borderRadius: 20,
            padding: 20,
            maxHeight: '90vh', overflowY: 'auto',
            boxShadow: '0 24px 60px rgba(0,0,0,0.24)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
              <button
                onClick={() => { setActive(null); setExplanation(null) }}
                aria-label="关闭"
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  border: 'none',
                  background: 'var(--bg)',
                  color: 'var(--muted)',
                  fontSize: 20,
                  lineHeight: 1,
                  cursor: 'pointer',
                }}
              >
                ×
              </button>
            </div>
            {/* FlashCard */}
            <FlashCard
              word={active}
              mode="browse"
              promptText={`${active.word}(${active.pinyin})`}
              answerLabel="释义"
              answerText={explanation?.explanation_zh ?? ''}
              answerSubText={[
                explanation?.pinyin,
                explanation?.source_type ? `${explanation.source_type}${explanation.source_confidence ? ` · ${explanation.source_confidence}` : ''}` : '',
                explanation?.source_text ?? '',
              ].filter(Boolean).join('\n')}
              revealLabel="查看释义"
              revealLoading={explaining}
              onReveal={handleExplain}
              onCorrect={() => handleMark(true)}
              onWrong={() => handleMark(false)}
            />

            {/* Error */}
            {explainError && (
              <div style={{ marginTop: 12, padding: '10px 14px', background: '#fee2e2', borderRadius: 10, fontSize: 13, color: '#dc2626' }}>
                {explainError}
              </div>
            )}

            {/* Explanation panel */}
            {explanation && (
              <div style={{ marginTop: 16 }}>
                {/* Pinyin + explanation */}
                <div style={{ padding: '14px 16px', background: 'var(--bg)', borderRadius: 12, marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: 'var(--primary)', fontWeight: 600, marginBottom: 8 }}>
                    {explanation.pinyin}
                  </div>
                  {(explanation.source_type || explanation.source_text) && (
                    <div style={{ marginBottom: 10, padding: '10px 12px', borderRadius: 10, background: '#fff', border: '1px solid var(--border)' }}>
                      {explanation.source_type && (
                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--primary)', marginBottom: explanation.source_text ? 6 : 0 }}>
                          {explanation.source_type}
                          {explanation.source_confidence ? ` · ${explanation.source_confidence}` : ''}
                        </div>
                      )}
                      {explanation.source_text && (
                        <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.6 }}>
                          {explanation.source_text}
                        </div>
                      )}
                    </div>
                  )}
                  <div style={{ fontSize: 14, color: 'var(--text)', lineHeight: 1.7, marginBottom: 8 }}>
                    {explanation.explanation_zh}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.6, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                    {explanation.explanation}
                  </div>
                </div>

                {/* Example sentences */}
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--muted)', marginBottom: 8 }}>例句</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {explanation.examples.map((ex, i) => (
                    <div key={i} style={{
                      padding: '12px 14px', borderRadius: 12,
                      background: ex.is_classical ? '#fdf6e3' : '#f8f9fa',
                      borderLeft: `3px solid ${ex.is_classical ? '#d4a017' : 'var(--border)'}`,
                    }}>
                      {ex.is_classical && (
                        <div style={{ fontSize: 10, color: '#d4a017', fontWeight: 600, marginBottom: 4 }}>
                          文言文
                        </div>
                      )}
                      <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 4, lineHeight: 1.5 }}>
                        {ex.sentence}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.5 }}>
                        {ex.translation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
