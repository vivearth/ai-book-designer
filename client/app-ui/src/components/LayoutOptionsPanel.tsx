import type { Book, Page, PageLayoutOption } from '../types'
import { LayoutOptionPreview } from './LayoutOptionPreview'

export function LayoutOptionsPanel({ open, page, book, options, selectedOptionId, generating, onClose, onPreview, onUseLayout, onRegenerate }: {
  open: boolean
  page: Page | null
  book: Book
  options: PageLayoutOption[]
  selectedOptionId?: string | null
  generating: boolean
  onClose: () => void
  onPreview: (option: PageLayoutOption) => void
  onUseLayout: (option: PageLayoutOption) => void
  onRegenerate: () => void
}) {
  if (!open || !page) return null

  return (
    <div className="export-modal-backdrop" role="dialog" aria-modal="true">
      <div className="layout-options-modal">
        <h3>Choose a layout for Page {page.page_number}</h3>
        <p className="muted">Generate layout options for the current text and images. Preview an option, then apply it to this page.</p>
        {generating ? <p className="notice-pill">Generating layout options…</p> : null}
        {options.length ? (
          <div className="layout-options-grid">
            {options.map((option) => (
              <div key={option.id}>
                <LayoutOptionPreview book={book} page={page} option={option} selected={selectedOptionId === option.id} onSelect={() => onPreview(option)} />
                <div className="chat-actions">
                  <button type="button" className="ghost-button" onClick={() => onPreview(option)}>Preview</button>
                  <button type="button" onClick={() => onUseLayout(option)}>Use this layout</button>
                </div>
              </div>
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
