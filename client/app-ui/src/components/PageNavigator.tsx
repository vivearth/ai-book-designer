import { useMemo, useState } from 'react'
import type { Page } from '../types'

export function PageNavigator({ pages, activePageId, onSelectPage, onCreateNext }: {
  pages: Page[]
  activePageId: string | null
  onSelectPage: (id: string | null) => void
  onCreateNext: () => void
}) {
  const [jump, setJump] = useState('')
  const sorted = [...pages].sort((a, b) => a.page_number - b.page_number)
  const active = sorted.find((p) => p.id === activePageId) ?? sorted[0] ?? null
  const windowed = useMemo(() => {
    if (!active) return sorted.slice(0, 10)
    return sorted.filter((p) => Math.abs(p.page_number - active.page_number) <= 5 || p.page_number <= 2 || p.page_number > sorted.length - 2)
  }, [sorted, active])

  return (
    <div className="page-navigator">
      <button type="button" onClick={() => onSelectPage(null)}>Cover</button>
      {windowed.map((p) => <button key={p.id} className={active?.id === p.id ? 'is-active' : ''} onClick={() => onSelectPage(p.id)}>P{p.page_number}</button>)}
      <span className="page-count">{sorted.length} pages</span>
      <input value={jump} onChange={(e) => setJump(e.target.value)} placeholder="Go to" />
      <button type="button" onClick={() => {
        const num = Number(jump)
        const found = sorted.find((p) => p.page_number === num)
        if (found) onSelectPage(found.id)
      }}>Jump</button>
      <button type="button" onClick={onCreateNext}>+ Next page</button>
    </div>
  )
}
