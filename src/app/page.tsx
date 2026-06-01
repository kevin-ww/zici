'use client'

import { useEffect, useState } from 'react'
import type { GradeMeta } from '@/types'
import { getGradeIndex } from '@/lib/data'
import { getAllProgress } from '@/lib/storage'
import UserMenu from '@/components/UserMenu'

export default function HomePage() {
  const [grades, setGrades] = useState<GradeMeta[]>([])
  const [mastered, setMastered] = useState<Record<string, number>>({})

  useEffect(() => {
    getGradeIndex().then(setGrades)
    getAllProgress().then(list => {
      const map: Record<string, number> = {}
      list.forEach(p => {
        if (p.status === 'mastered') {
          // key: grade-semester derived from wordId prefix "7-1-..."
          const [g, s] = p.wordId.split('-')
          const key = `${g}-${s}`
          map[key] = (map[key] ?? 0) + 1
        }
      })
      setMastered(map)
    })
  }, [])

  const gradeGroups: Record<number, GradeMeta[]> = {}
  grades.forEach(g => {
    if (!gradeGroups[g.grade]) gradeGroups[g.grade] = []
    gradeGroups[g.grade].push(g)
  })

  const gradeNames: Record<number, string> = { 7: '初一', 8: '初二', 9: '初三' }

  return (
    <div style={{ padding: '24px 16px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700 }}>字词通</h1>
        <UserMenu />
      </div>
      <p style={{ color: 'var(--muted)', fontSize: 14, marginBottom: 24 }}>初中语文重点字词</p>

      {Object.entries(gradeGroups).map(([grade, semesters]) => (
        <div key={grade} style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--muted)', marginBottom: 12 }}>
            {gradeNames[Number(grade)]}
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {semesters.map(s => {
              const key = `${s.grade}-${s.semester}`
              const m = mastered[key] ?? 0
              const pct = s.total > 0 ? Math.round((m / s.total) * 100) : 0
              return (
                <a key={s.label} href={`/grade/${s.grade}-${s.semester}`}
                  style={{ textDecoration: 'none', color: 'inherit' }}>
                  <div className="card" style={{ padding: '16px', cursor: 'pointer' }}>
                    <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>{s.label}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 10 }}>
                      {s.total} 个字词
                    </div>
                    <div style={{
                      height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden'
                    }}>
                      <div style={{
                        height: '100%', width: `${pct}%`,
                        background: 'var(--primary)', borderRadius: 3,
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                      已掌握 {pct}%
                    </div>
                  </div>
                </a>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
