import type { Page } from '../types'

export function PagePreview({ page, mode }: { page: Page | null; mode: string }) {
  const image = page?.images?.[0]
  const text = page?.final_text || page?.generated_text || page?.user_text || 'Your next page will appear here as soon as you start shaping it.'

  return (
    <div className={`page-preview page-preview--${mode}`}>
      {image && mode !== 'text-only' ? <img src={`/api/uploads/${image.stored_filename}`} alt={image.original_filename} className="page-preview__image" /> : null}
      <div className="page-preview__body">
        <div className="page-preview__meta">{page ? `Page ${page.page_number}` : 'Preview page'}</div>
        <article>{text}</article>
      </div>
    </div>
  )
}
