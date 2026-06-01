'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'

export default function LoginPage() {
  const { login, register } = useAuth()
  const router = useRouter()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      if (mode === 'login') {
        await login(email, password)
      } else {
        await register(email, password, displayName || undefined)
      }
      router.replace('/')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '操作失败，请重试')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24, background: 'var(--bg)',
    }}>
      <div className="card" style={{ width: '100%', maxWidth: 380, padding: 32 }}>
        <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4, textAlign: 'center' }}>字词</h1>
        <p style={{ color: 'var(--muted)', fontSize: 13, textAlign: 'center', marginBottom: 28 }}>
          Mandarin Vocabulary
        </p>

        {/* Mode toggle */}
        <div style={{ display: 'flex', background: 'var(--border)', borderRadius: 10, padding: 3, marginBottom: 24 }}>
          {(['login', 'register'] as const).map(m => (
            <button key={m} onClick={() => setMode(m)} style={{
              flex: 1, padding: '7px 0', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 14,
              background: mode === m ? '#fff' : 'transparent',
              color: mode === m ? 'var(--text)' : 'var(--muted)',
              fontWeight: mode === m ? 600 : 400,
            }}>
              {m === 'login' ? '登录' : '注册'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {mode === 'register' && (
            <input
              type="text" placeholder="显示名称（可选）" value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              style={inputStyle}
            />
          )}
          <input
            type="email" placeholder="邮箱" value={email} required
            onChange={e => setEmail(e.target.value)}
            style={inputStyle}
          />
          <input
            type="password" placeholder="密码" value={password} required
            onChange={e => setPassword(e.target.value)}
            style={inputStyle}
          />

          {error && (
            <div style={{ color: '#dc2626', fontSize: 13, padding: '8px 12px', background: '#fee2e2', borderRadius: 8 }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={submitting} style={{
            padding: '13px', borderRadius: 12, border: 'none', cursor: submitting ? 'default' : 'pointer',
            background: submitting ? 'var(--muted)' : 'var(--primary)',
            color: '#fff', fontSize: 15, fontWeight: 600, marginTop: 4,
          }}>
            {submitting ? '请稍候...' : mode === 'login' ? '登录' : '注册'}
          </button>
        </form>

        <p style={{ color: 'var(--muted)', fontSize: 12, textAlign: 'center', marginTop: 20 }}>
          演示账号: demo@zici.app / demo1234
        </p>
      </div>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  padding: '12px 14px', borderRadius: 10, border: '1.5px solid var(--border)',
  fontSize: 15, outline: 'none', background: '#fff', color: 'var(--text)',
  fontFamily: 'inherit', width: '100%', boxSizing: 'border-box',
}
