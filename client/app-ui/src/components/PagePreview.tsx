import { resolveUploadUrl } from '../api'
import type { Book, Page } from '../types'

function InternalImagePlaceholder({ layoutId }: { layoutId: string }) {
  return (
    <div className={`internal-image-placeholder internal-image-placeholder--${layoutId}`}>
      <div className="scene-illustration">
        <div className="scene-illustration__sun" />
        <div className="scene-illustration__hill scene-illustration__hill--back" />
        <div className="scene-illustration__hill scene-illustration__hill--front" />
        <div className="scene-illustration__tree" />
      </div>
    </div>
  )
}

export function PagePreview({ book, page }: { book: Book; page: Page | null }) {
  const layoutId = book.format_settings?.selected_layout_id || book.layout_template
  const composition = (page?.layout_json?.composition as string | undefined) || (page?.images?.length ? 'text-with-image' : 'text_only')
  const image = page?.images?.[0]
  const text = page?.final_text || page?.generated_text || page?.user_text || 'Your next page will appear here as soon as you start shaping it.'
  const showImageArea = composition !== 'text_only'

  return (
    <div className={`page-preview page-preview--${layoutId} page-preview--${composition}`}>
      <div className="page-preview__meta">{page ? `Page ${page.page_number}` : 'Preview page'}</div>
      {showImageArea ? (
        image ? <img src={resolveUploadUrl(image.stored_filename)} alt={image.original_filename} className="page-preview__image" /> : <InternalImagePlaceholder layoutId={layoutId} />
      ) : null}
      <div className="page-preview__body">
        {layoutId === 'modern-editorial' ? <div className="page-preview__headline">Designed with editorial hierarchy in mind</div> : null}
        {layoutId === 'classic-novel' ? <div className="page-preview__chapter-label">Chapter draft</div> : null}
        <article>{text}</article>
        {layoutId === 'modern-editorial' ? <aside className="page-preview__callout">Pull quote / callout space</aside> : null}
      </div>
    </div>
  )
}
