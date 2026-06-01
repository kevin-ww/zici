'use client'

import { useEffect, useState } from 'react'
import { apiCreateQuiz, apiSubmitQuiz, type QuizQuestion, type QuizResult } from '@/lib/api'

interface ActiveQuiz {
  attemptId: string
  questions: QuizQuestion[]
  answers: { word_id: string; selected_answer: string }[]
}

export default function QuizPage() {
  const [quiz, setQuiz] = useState<ActiveQuiz | null>(null)
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [results, setResults] = useState<QuizResult[] | null>(null)
  const [score, setScore] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  async function buildQuiz() {
    setLoading(true)
    setResults(null)
    setScore(0)
    try {
      const data = await apiCreateQuiz(10)
      setQuiz({ attemptId: data.quiz_attempt_id, questions: data.questions, answers: [] })
      setCurrent(0)
      setSelected(null)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { buildQuiz() }, [])

  function handleSelect(opt: string) {
    if (selected || !quiz) return
    setSelected(opt)
    const q = quiz.questions[current]
    setQuiz(prev => prev ? {
      ...prev,
      answers: [...prev.answers, { word_id: q.word_id, selected_answer: opt }]
    } : prev)
  }

  async function handleNext() {
    if (!quiz) return
    if (current + 1 >= quiz.questions.length) {
      setSubmitting(true)
      try {
        const res = await apiSubmitQuiz(quiz.attemptId, quiz.answers)
        setResults(res.results)
        setScore(res.score)
      } catch (e) {
        console.error(e)
      } finally {
        setSubmitting(false)
      }
    } else {
      setCurrent(c => c + 1)
      setSelected(null)
    }
  }

  if (loading) return <div style={{ padding: 24, color: 'var(--muted)' }}>生成题目中...</div>

  if (results) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <div style={{ fontSize: 56, marginBottom: 16 }}>
          {score >= 8 ? '🏆' : score >= 6 ? '👏' : '📖'}
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
          {score} / {results.length}
        </div>
        <div style={{ color: 'var(--muted)', marginBottom: 24 }}>
          {score >= 8 ? '太棒了！' : score >= 6 ? '继续加油！' : '多加练习，下次会更好！'}
        </div>
        <button onClick={buildQuiz} style={{
          padding: '12px 32px', borderRadius: 12, border: 'none', cursor: 'pointer',
          background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 600,
        }}>再来一组</button>
      </div>
    )
  }

  if (!quiz) return null
  const q = quiz.questions[current]

  return (
    <div style={{ padding: '20px 16px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700 }}>拼音自测</h1>
        <span style={{ color: 'var(--muted)', fontSize: 14 }}>{current + 1} / {quiz.questions.length}</span>
      </div>

      <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, marginBottom: 24, overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${((current + 1) / quiz.questions.length) * 100}%`,
          background: 'var(--primary)', borderRadius: 3, transition: 'width 0.3s'
        }} />
      </div>

      <div className="card" style={{ padding: 28, marginBottom: 20, textAlign: 'center' }}>
        <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>下列哪个是正确拼音？</div>
        <div style={{ fontSize: 52, fontWeight: 700, letterSpacing: 4 }}>{q.word}</div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {q.options.map((opt, index) => {
          // before submitting we don't know the correct answer — revealed after submit
          const isSelected = opt === selected
          let bg = '#fff', border = 'var(--border)', color = 'var(--text)'
          if (selected) {
            if (isSelected) { bg = '#dbeafe'; border = 'var(--primary)'; color = 'var(--primary)' }
          }
          return (
            <button key={opt} data-demo={`quiz-option-${index}`} onClick={() => handleSelect(opt)} style={{
              padding: '14px 20px', borderRadius: 12, border: `2px solid ${border}`,
              background: bg, color, fontSize: 16, cursor: selected ? 'default' : 'pointer',
              textAlign: 'left', fontFamily: 'inherit',
            }}>
              {opt}
            </button>
          )
        })}
      </div>

      {selected && (
        <button data-demo="quiz-next" onClick={handleNext} disabled={submitting} style={{
          width: '100%', marginTop: 20, padding: '14px', borderRadius: 12,
          border: 'none', cursor: submitting ? 'default' : 'pointer',
          background: submitting ? 'var(--muted)' : 'var(--primary)',
          color: '#fff', fontSize: 15, fontWeight: 600,
        }}>
          {submitting ? '提交中...' : current + 1 >= quiz.questions.length ? '查看结果' : '下一题 →'}
        </button>
      )}
    </div>
  )
}
