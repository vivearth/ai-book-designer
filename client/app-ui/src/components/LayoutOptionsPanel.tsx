import type { Book, Page, PageLayoutOption } from '../types'
import { LayoutOptionPreview } from './LayoutOptionPreview'

export function LayoutOptionsPanel({ open, page, book, options, selectedOptionId, generating, onClose, onSelect, onRegenerate }: {
  open: boolean
  page: Page | null
  book: Book
  options: PageLayoutOption[]
  selectedOptionId?: string | null
  generating: boolean
  onClose: () => void
  onSelect: (option: PageLayoutOption) => void
  onRegenerate: () => void
}) {
  if (!open || !page) return null

  return (
    <div className="export-modal-backdrop" role="dialog" aria-modal="true">
      <div className="layout-options-modal">
        <h3>Choose a layout for Page {page.page_number}</h3>
        <p className="muted">Compare Option A and Option B side by side, then select one to apply to preview and export.</p>
        {generating ? <p className="notice-pill">Generating layout options…</p> : null}
        {options.length ? (
          <div className="layout-options-grid">
            {options.map((option) => (
              <LayoutOptionPreview
                key={option.id}
                book={book}
                page={page}
                option={option}
                selected={selectedOptionId === option.id}
                onSelect={() => onSelect(option)}
              />
            ))}
          </div>
        ) : (
          <p className="muted">No saved layout options yet. Generate options to compare this page.</p>
        )}
        <div className="chat-actions">
          <button type="button" onClick={onRegenerate} disabled={generating}>Regenerate options</button>
          <button type="button" className="ghost-button" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
