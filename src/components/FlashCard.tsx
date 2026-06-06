'use client'

import { useEffect, useState } from 'react'
import type { Character } from '@/types'
import { speak } from '@/lib/tts'

interface Props {
  word: Character
  mode?: 'browse' | 'review'
  promptLabel?: string
  promptText?: string
  answerLabel?: string
  answerText?: string
  answerSubText?: string
  revealLabel?: string
  revealLoading?: boolean
  onReveal?: () => Promise<boolean | void> | boolean | void
  onCorrect: () => void
  onWrong: () => void
}

export default function FlashCard({
  word,
  mode = 'browse',
  promptLabel = '拼音',
  promptText,
  answerLabel = '答案',
  answerText,
  answerSubText,
  revealLabel,
  revealLoading = false,
  onReveal,
  onCorrect,
  onWrong,
}: Props) {
  const [flipped, setFlipped] = useState(false)

  useEffect(() => {
    setFlipped(false)
  }, [word.id, promptText, mode])

  const typeLabel: Record<string, string> = { char: '字', word: '词语', idiom: '成语' }
  const frontValue = promptText ?? word.word
  const backValue = answerText ?? word.pinyin
  const promptAction = revealLabel ?? (promptLabel === '释义' ? '查看释义' : '查看拼音')
  const frontFontSize = frontValue.length > 12 ? 30 : frontValue.length > 8 ? 38 : 52
  const answerFontSize = backValue.length > 12 ? 18 : backValue.length > 8 ? 20 : 22
  const actionButton = (
    <button onClick={async () => {
      try {
        const result = await onReveal?.()
        if (result === false) return
        if (mode === 'review') {
          setFlipped(true)
        }
      } catch {
        // parent handles the error state
      }
    }} disabled={revealLoading} style={{
      width: '100%', padding: '12px', borderRadius: 12, border: 'none',
      background: revealLoading ? 'var(--border)' : 'var(--primary)',
      color: revealLoading ? 'var(--muted)' : '#fff',
      fontSize: 15, fontWeight: 600,
      cursor: revealLoading ? 'default' : 'pointer',
      marginTop: 16,
    }}>
      {revealLoading ? '加载中...' : promptAction}
    </button>
  )

  return (
    <div className="card" style={{ padding: 28, userSelect: 'none' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, alignItems: 'center' }}>
        <span style={{
          fontSize: 11, padding: '3px 10px', borderRadius: 20,
          background: 'var(--primary-light)', color: 'var(--primary)',
        }}>
          {typeLabel[word.type]}
        </span>
        <button onClick={() => speak(word.word)} style={{
          border: 'none', background: 'none', cursor: 'pointer', fontSize: 20,
        }}>
          🔊
        </button>
      </div>

      <div style={{ textAlign: 'center', marginBottom: 20 }}>
        <div style={{
          fontSize: frontFontSize,
          fontWeight: 700,
          letterSpacing: frontValue.length > 8 ? 1 : 4,
          marginBottom: 10,
          lineHeight: 1.35,
          whiteSpace: 'pre-wrap',
        }}>
          {frontValue}
        </div>
        {mode === 'browse' && actionButton}
      </div>

      {flipped ? (
        <div style={{
          background: 'var(--primary-light)', borderRadius: 12, padding: '14px 20px',
          textAlign: 'center', marginBottom: 20,
        }}>
          <div style={{ fontSize: 13, color: 'var(--primary)', fontWeight: 600, marginBottom: 6 }}>
            {answerLabel}
          </div>
          <div style={{
            fontSize: answerFontSize,
            color: 'var(--primary)',
            fontWeight: 700,
            letterSpacing: backValue.length > 8 ? 1 : 3,
            lineHeight: 1.4,
            whiteSpace: 'pre-wrap',
          }}>
            {backValue}
          </div>
          {answerSubText && (
            <div style={{ marginTop: 8, fontSize: 15, color: 'var(--primary)', opacity: 0.85, lineHeight: 1.4, whiteSpace: 'pre-wrap' }}>
              {answerSubText}
            </div>
          )}
          {promptLabel === '释义' && (
            <div style={{ marginTop: 8, fontSize: 12, color: 'var(--muted)', lineHeight: 1.5 }}>
              {word.word} · {word.pinyin}
            </div>
          )}
        </div>
      ) : null}

      {flipped ? (
        <div style={{ display: 'flex', gap: 12 }}>
          <button data-demo="flashcard-wrong" onClick={onWrong} style={{
            flex: 1, padding: '12px', borderRadius: 12, border: 'none', cursor: 'pointer',
            background: '#fee2e2', color: '#dc2626', fontSize: 15, fontWeight: 600,
          }}>
            ✗ 没记住
          </button>
          <button data-demo="flashcard-correct" onClick={onCorrect} style={{
            flex: 1, padding: '12px', borderRadius: 12, border: 'none', cursor: 'pointer',
            background: '#dcfce7', color: '#16a34a', fontSize: 15, fontWeight: 600,
          }}>
            ✓ 记住了
          </button>
        </div>
      ) : mode === 'review' ? actionButton : null}
    </div>
  )
}
