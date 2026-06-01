import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/lib/auth'
import AuthGate from '@/components/AuthGate'

export const metadata: Metadata = {
  title: '字词通 — 初中语文字词记忆',
  description: '帮助初中生系统记忆语文重点字词',
  manifest: '/manifest.json',
  themeColor: '#6366f1',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: '字词通',
  },
  icons: {
    apple: '/icons/icon-192.png',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <AuthProvider>
          <AuthGate>
            <main style={{ paddingBottom: '80px' }}>{children}</main>
            <nav style={{
              position: 'fixed', bottom: 0, left: '50%', transform: 'translateX(-50%)',
              width: '100%', maxWidth: 480, background: '#fff',
              borderTop: '1px solid var(--border)', display: 'flex',
              justifyContent: 'space-around', padding: '10px 0 20px',
              zIndex: 100,
            }}>
              <a href="/" style={navStyle}>
                <span style={{ fontSize: 22 }}>📚</span>
                <span style={{ fontSize: 11, marginTop: 2 }}>字词库</span>
              </a>
              <a href="/review" style={navStyle}>
                <span style={{ fontSize: 22 }}>🔄</span>
                <span style={{ fontSize: 11, marginTop: 2 }}>复习</span>
              </a>
              <a href="/quiz" style={navStyle}>
                <span style={{ fontSize: 22 }}>✏️</span>
                <span style={{ fontSize: 11, marginTop: 2 }}>自测</span>
              </a>
              <a href="/stats" style={navStyle}>
                <span style={{ fontSize: 22 }}>📊</span>
                <span style={{ fontSize: 11, marginTop: 2 }}>统计</span>
              </a>
            </nav>
          </AuthGate>
        </AuthProvider>
      </body>
    </html>
  )
}

const navStyle: React.CSSProperties = {
  display: 'flex', flexDirection: 'column', alignItems: 'center',
  textDecoration: 'none', color: 'var(--muted)', flex: 1,
}
