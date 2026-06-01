'use client'

import { useEffect, useState } from 'react'
import { apiGetStatsByGrade, apiGetStatsOverview, type StatsByGrade, type StatsOverview } from '@/lib/api'

export default function StatsPage() {
  const [overview, setOverview] = useState<StatsOverview | null>(null)
  const [byGrade, setByGrade] = useState<StatsByGrade[]>([])

  useEffect(() => {
    Promise.all([apiGetStatsOverview(), apiGetStatsByGrade()])
      .then(([ov, bg]) => { setOverview(ov); setByGrade(bg) })
      .catch(console.error)
  }, [])

  const pct = overview?.mastered_percent ?? 0

  return (
    <div style={{ padding: '20px 16px 0' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>学习统计</h1>

      {/* Overall */}
      <div className="card" style={{ padding: 24, marginBottom: 20, textAlign: 'center' }}>
        <div style={{ fontSize: 48, fontWeight: 800, color: 'var(--primary)' }}>{pct}%</div>
        <div style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 16 }}>总体掌握率</div>
        <div style={{ height: 10, background: 'var(--border)', borderRadius: 5, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${pct}%`,
            background: 'var(--primary)', borderRadius: 5, transition: 'width 0.5s'
          }} />
        </div>
      </div>

      {/* Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
        {[
          { label: '已掌握', value: overview?.mastered ?? 0, color: 'var(--mastered)' },
          { label: '学习中', value: overview?.learning ?? 0, color: 'var(--learning)' },
          { label: '未学', value: overview?.new_count ?? 0, color: 'var(--new)' },
        ].map(item => (
          <div key={item.label} className="card" style={{ padding: 16, textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: item.color }}>{item.value}</div>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>{item.label}</div>
          </div>
        ))}
      </div>

      {/* Per grade */}
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>各册进度</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {byGrade.map(g => {
          const key = `${g.grade}-${g.semester}`
          const p = g.mastered_percent
          const label = `${['', '', '', '', '', '', '', '七', '八', '九'][g.grade]}年级${g.semester === 1 ? '上' : '下'}册`
          return (
            <div key={key} className="card" style={{ padding: '14px 16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 14, fontWeight: 500 }}>{label}</span>
                <span style={{ fontSize: 13, color: 'var(--muted)' }}>{g.mastered}/{g.total}</span>
              </div>
              <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', width: `${p}%`,
                  background: p === 100 ? 'var(--mastered)' : 'var(--primary)', borderRadius: 3,
                }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
