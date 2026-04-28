import { useMemo } from 'react'
import type { Page } from '../types'

type ActiveTarget = { kind: 'cover' } | { kind: 'page'; pageId: string } | { kind: 'new-page' }

export function PageNavigator({ pages, activeTarget, onSelectCover, onSelectPage, onCreateNext }: {
  pages: Page[]
  activeTarget: ActiveTarget
  onSelectCover: () => void
  onSelectPage: (id: string) => void
  onCreateNext: () => void
}) {
  const sorted = [...pages].sort((a, b) => a.page_number - b.page_number)
  const active = activeTarget.kind === 'page' ? sorted.find((p) => p.id === activeTarget.pageId) ?? null : null
  const activeIndex = useMemo(() => (active ? sorted.findIndex((p) => p.id === active.id) : -1), [sorted, active])
  const canPrev = activeTarget.kind === 'page' ? activeIndex >= 0 : false
  const canNext = activeTarget.kind === 'cover' ? sorted.length > 0 : activeIndex >= 0 && activeIndex < sorted.length - 1

  return (
    <div className="page-navigator compact-toolbar">
      <button type="button" className={`icon-btn ${activeTarget.kind === 'cover' ? 'is-active' : ''}`} title="Cover" aria-label="Cover" onClick={onSelectCover}>◉</button>
      <button type="button" className="icon-btn" title="Previous page" aria-label="Previous page" disabled={!canPrev} onClick={() => {
        if (activeTarget.kind !== 'page') return
        if (activeIndex === 0) onSelectCover()
        else onSelectPage(sorted[activeIndex - 1].id)
      }}>‹</button>
      <span className="page-count">{active ? `${active.page_number}` : 'Cover'} / {sorted.length || 0}</span>
      <button type="button" className="icon-btn" title="Next page" aria-label="Next page" disabled={!canNext} onClick={() => {
        if (activeTarget.kind === 'cover') {
          if (sorted[0]) onSelectPage(sorted[0].id)
          return
        }
        if (canNext) onSelectPage(sorted[activeIndex + 1].id)
      }}>›</button>
      <button type="button" className="icon-btn" title="Add page" aria-label="Add page" onClick={onCreateNext}>＋</button>
    </div>
  )
}
