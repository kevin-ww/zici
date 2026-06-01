'use client'

import { useEffect, useState } from 'react'
import type { Character } from '@/types'
import { apiGetDue, apiMarkWord } from '@/lib/api'
import FlashCard from '@/components/FlashCard'

export default function ReviewPage() {
  const [queue, setQueue] = useState<Character[]>([])
  const [current, setCurrent] = useState(0)
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiGetDue(30)
      .then(items => setQueue(items.map(({ progress: _p, ...w }) => w as Character)))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

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

  const word = queue[current]

  return (
    <div style={{ padding: '20px 16px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700 }}>今日复习</h1>
        <span style={{ color: 'var(--muted)', fontSize: 14 }}>{current + 1} / {queue.length}</span>
      </div>

      <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, marginBottom: 24, overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${((current + 1) / queue.length) * 100}%`,
          background: 'var(--primary)', borderRadius: 3, transition: 'width 0.3s'
        }} />
      </div>

      <FlashCard word={word} onCorrect={() => handleAnswer(true)} onWrong={() => handleAnswer(false)} />
    </div>
  )
}
