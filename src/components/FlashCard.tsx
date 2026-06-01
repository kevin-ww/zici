'use client'

import { useState } from 'react'
import type { Character } from '@/types'
import { speak } from '@/lib/tts'

interface Props {
  word: Character
  onCorrect: () => void
  onWrong: () => void
}

export default function FlashCard({ word, onCorrect, onWrong }: Props) {
  const [flipped, setFlipped] = useState(false)

  const typeLabel: Record<string, string> = { char: '字', word: '词语', idiom: '成语' }

  return (
    <div className="card" style={{ padding: 28, userSelect: 'none' }}>
      {/* Tag */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, alignItems: 'center' }}>
        <span style={{
          fontSize: 11, padding: '3px 10px', borderRadius: 20,
          background: 'var(--primary-light)', color: 'var(--primary)',
        }}>{typeLabel[word.type]}</span>
        <button onClick={() => speak(word.word)} style={{
          border: 'none', background: 'none', cursor: 'pointer', fontSize: 20,
        }}>🔊</button>
      </div>

      {/* Front: character */}
      <div style={{ textAlign: 'center', marginBottom: 20 }}>
        <div style={{ fontSize: 56, fontWeight: 700, letterSpacing: 4, marginBottom: 8 }}>
          {word.word}
        </div>
        {!flipped && (
          <div style={{ fontSize: 13, color: 'var(--muted)' }}>点击查看拼音</div>
        )}
      </div>

      {/* Back: pinyin */}
      {flipped ? (
        <div style={{
          background: 'var(--primary-light)', borderRadius: 12, padding: '14px 20px',
          textAlign: 'center', marginBottom: 20,
        }}>
          <div style={{ fontSize: 22, color: 'var(--primary)', fontWeight: 500, letterSpacing: 3 }}>
            {word.pinyin}
          </div>
        </div>
      ) : (
        <div
          onClick={() => setFlipped(true)}
          style={{
            background: 'var(--border)', borderRadius: 12, padding: '14px 20px',
            textAlign: 'center', marginBottom: 20, cursor: 'pointer',
          }}
        >
          <div style={{ fontSize: 14, color: 'var(--muted)' }}>点击翻转</div>
        </div>
      )}

      {/* Action buttons */}
      {flipped ? (
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={onWrong} style={{
            flex: 1, padding: '12px', borderRadius: 12, border: 'none', cursor: 'pointer',
            background: '#fee2e2', color: '#dc2626', fontSize: 15, fontWeight: 600,
          }}>
            ✗ 没记住
          </button>
          <button onClick={onCorrect} style={{
            flex: 1, padding: '12px', borderRadius: 12, border: 'none', cursor: 'pointer',
            background: '#dcfce7', color: '#16a34a', fontSize: 15, fontWeight: 600,
          }}>
            ✓ 记住了
          </button>
        </div>
      ) : (
        <button onClick={() => setFlipped(true)} style={{
          width: '100%', padding: '12px', borderRadius: 12, border: 'none', cursor: 'pointer',
          background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 600,
        }}>
          查看拼音
        </button>
      )}
    </div>
  )
}
