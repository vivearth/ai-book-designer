import { useMemo, useState } from 'react'
import type { Page } from '../types'

export function PageNavigator({ pages, activePageId, isCoverActive, onSelectCover, onSelectPage, onCreateNext }: {
  pages: Page[]
  activePageId: string | null
  isCoverActive: boolean
  onSelectCover: () => void
  onSelectPage: (id: string) => void
  onCreateNext: () => void
}) {
  const [jump, setJump] = useState('')
  const sorted = [...pages].sort((a, b) => a.page_number - b.page_number)
  const active = sorted.find((p) => p.id === activePageId) ?? null
  const activeIndex = useMemo(() => (active ? sorted.findIndex((p) => p.id === active.id) : -1), [sorted, active])
  const canPrev = activeIndex > 0
  const canNext = activeIndex >= 0 && activeIndex < sorted.length - 1

  return (
    <div className="page-navigator">
      <button type="button" className={`icon-btn ${isCoverActive ? 'is-active' : ''}`} onClick={onSelectCover} title="Cover">📘</button>
      <button type="button" className="icon-btn" disabled={!canPrev} onClick={() => canPrev && onSelectPage(sorted[activeIndex - 1].id)}>‹</button>
      <span className="page-count">{active ? `Page ${active.page_number} of ${sorted.length}` : `Page 0 of ${sorted.length}`}</span>
      <button type="button" className="icon-btn" disabled={!canNext} onClick={() => canNext && onSelectPage(sorted[activeIndex + 1].id)}>›</button>
      <input className="jump-input" value={jump} onChange={(e) => setJump(e.target.value)} placeholder="Jump" />
      <button type="button" className="icon-btn" onClick={() => {
        const num = Number(jump)
        const found = sorted.find((p) => p.page_number === num)
        if (found) onSelectPage(found.id)
      }}>↳</button>
      <button type="button" className="icon-btn" onClick={onCreateNext}>＋</button>
    </div>
  )
}
