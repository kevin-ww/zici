'use client'

import { useEffect, useRef, useState } from 'react'
import { useAuth } from '@/lib/auth'

export default function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // close on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  if (!user) return null

  const initials = (user.displayName ?? user.email)
    .split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      {/* Avatar button */}
      <button onClick={() => setOpen(o => !o)} style={{
        width: 34, height: 34, borderRadius: '50%',
        background: 'var(--primary)', color: '#fff',
        border: 'none', cursor: 'pointer',
        fontSize: 13, fontWeight: 700,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        {initials}
      </button>

      {/* Dropdown */}
      {open && (
        <div style={{
          position: 'absolute', top: 42, right: 0,
          background: '#fff', borderRadius: 12,
          border: '1px solid var(--border)',
          boxShadow: '0 4px 20px rgba(0,0,0,0.12)',
          minWidth: 200, zIndex: 300, overflow: 'hidden',
        }}>
          {/* Profile info */}
          <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)' }}>
            <div style={{
              width: 40, height: 40, borderRadius: '50%',
              background: 'var(--primary)', color: '#fff',
              fontSize: 16, fontWeight: 700,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 10,
            }}>
              {initials}
            </div>
            {user.displayName && (
              <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 2 }}>
                {user.displayName}
              </div>
            )}
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>{user.email}</div>
          </div>

          {/* Logout */}
          <button onClick={() => { setOpen(false); logout() }} style={{
            width: '100%', padding: '12px 16px',
            background: 'none', border: 'none', cursor: 'pointer',
            textAlign: 'left', fontSize: 14, color: '#dc2626',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span>退出登录</span>
          </button>
        </div>
      )}
    </div>
  )
}
