import { useMemo, useState } from 'react'
import type { Page } from '../types'

type ActiveTarget = { kind: 'cover' } | { kind: 'page'; pageId: string } | { kind: 'new-page' }

export function PageNavigator({ pages, activeTarget, onSelectCover, onSelectPage, onCreateNext }: {
  pages: Page[]
  activeTarget: ActiveTarget
  onSelectCover: () => void
  onSelectPage: (id: string) => void
  onCreateNext: () => void
}) {
  const [jump, setJump] = useState('')
  const sorted = [...pages].sort((a, b) => a.page_number - b.page_number)
  const active = activeTarget.kind === 'page' ? sorted.find((p) => p.id === activeTarget.pageId) ?? null : null
  const activeIndex = useMemo(() => (active ? sorted.findIndex((p) => p.id === active.id) : -1), [sorted, active])
  const canPrev = activeTarget.kind === 'page' ? activeIndex >= 0 : false
  const canNext = activeTarget.kind === 'cover' ? sorted.length > 0 : activeIndex >= 0 && activeIndex < sorted.length - 1

  return (
    <div className="page-navigator">
      <button type="button" className={`icon-btn ${activeTarget.kind === 'cover' ? 'is-active' : ''}`} onClick={onSelectCover} title="Cover">Cover</button>
      <button type="button" className="icon-btn" disabled={!canPrev} onClick={() => {
        if (activeTarget.kind !== 'page') return
        if (activeIndex === 0) onSelectCover()
        else onSelectPage(sorted[activeIndex - 1].id)
      }}>Prev</button>
      <span className="page-count">{active ? `Page ${active.page_number} / ${sorted.length}` : `Cover / ${sorted.length}`}</span>
      <button type="button" className="icon-btn" disabled={!canNext} onClick={() => {
        if (activeTarget.kind === 'cover') {
          if (sorted[0]) onSelectPage(sorted[0].id)
          return
        }
        if (canNext) onSelectPage(sorted[activeIndex + 1].id)
      }}>Next</button>
      <button type="button" className="icon-btn" onClick={onCreateNext}>Add page</button>
      <details>
        <summary>Jump</summary>
        <div className="jump-popover">
          <input className="jump-input" value={jump} onChange={(e) => setJump(e.target.value)} placeholder="Page #" />
          <button type="button" className="icon-btn" onClick={() => {
            const found = sorted.find((p) => p.page_number === Number(jump))
            if (found) onSelectPage(found.id)
          }}>Go</button>
        </div>
      </details>
    </div>
  )
}
