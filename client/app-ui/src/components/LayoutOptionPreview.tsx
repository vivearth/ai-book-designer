import type { Book, Page, PageLayoutOption } from '../types'
import { PagePreview } from './PagePreview'

export function LayoutOptionPreview({ book, page, option, selected, onSelect }: {
  book: Book
  page: Page
  option: PageLayoutOption
  selected: boolean
  onSelect: () => void
}) {
  const overflowWarning = typeof option.layout_json?.overflow_warning === 'string' ? option.layout_json.overflow_warning : null

  return (
    <article className={`layout-option-card ${selected ? 'is-selected' : ''}`}>
      <header>
        <p className="chat-message__eyebrow">{option.label}</p>
        <h4>{(option.layout_json?.variant as string | undefined)?.split('_').join(' ') || 'Layout option'}</h4>
        <p>{option.rationale || (option.layout_json?.visual_intent as string | undefined) || 'Layout variation generated for this page.'}</p>
      </header>
      <div className="layout-option-card__preview">
        <PagePreview book={book} page={page} layoutOverride={option.layout_json} mini />
      </div>
      {overflowWarning ? <p className="warning-banner">{overflowWarning}</p> : null}
      <button type="button" className={selected ? 'secondary-button' : ''} onClick={onSelect}>{selected ? 'Selected' : `Use ${option.label}`}</button>
    </article>
  )
}
