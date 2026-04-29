import { useEffect, useState } from 'react'
import { resolveUploadUrl } from '../api'
import type { Book, Page } from '../types'
import { estimatePageCapacity } from '../utils/pageCapacity'

function InternalImagePlaceholder({ layoutId }: { layoutId: string }) {
  return <div className={`internal-image-placeholder internal-image-placeholder--${layoutId}`} />
}

export function PagePreview({ book, page, layoutOverride, mini = false, editable = false, onTextSave, onImageSelect }: { book: Book; page: Page | null; layoutOverride?: Record<string, unknown> | null; mini?: boolean; editable?: boolean; onTextSave?: (nextText: string) => Promise<void> | void; onImageSelect?: (imageId: string) => void }) {
  const layoutId = book.format_settings?.selected_layout_id || book.layout_template
  const activeLayout = layoutOverride || page?.layout_json || {}
  const composition = (activeLayout?.composition as string | undefined) || (page?.images?.length ? 'text-with-image' : 'text_only')
  const image = page?.images?.[0]
  const text = page?.final_text || page?.generated_text || page?.user_text || 'Your next page will appear here as soon as you start shaping it.'
  const capacity = estimatePageCapacity(book, page)
  const words = text.trim().split(/\s+/)
  const truncated = words.length > capacity.estimated_words
  const visibleText = truncated ? `${words.slice(0, capacity.estimated_words).join(' ')}…` : text
  const showImageArea = composition !== 'text_only'
  const headline = typeof page?.generation_metadata?.headline === 'string' ? String(page.generation_metadata.headline).trim() : null
  const canEdit = editable && !mini
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draftText, setDraftText] = useState(text)
  useEffect(() => setDraftText(text), [text, page?.id])

  async function saveIfChanged() {
    if (saving) return
    if (draftText === text) return setEditing(false)
    setSaving(true)
    try {
      await onTextSave?.(draftText)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={`page-preview page-preview--${layoutId} page-preview--${composition} ${mini ? 'page-preview--mini' : ''}`}>
      <div className="page-preview__meta">{page ? `Page ${page.page_number}` : 'Preview page'}</div>
      {showImageArea ? (image ? <img src={resolveUploadUrl(image.stored_filename)} alt={image.original_filename} className="page-preview__image" onDoubleClick={() => onImageSelect?.(image.id)} /> : <InternalImagePlaceholder layoutId={layoutId} />) : null}
      <div className="page-preview__body">
        {layoutId === 'modern-editorial' ? <div className="page-preview__headline">{headline || `Page ${page?.page_number || ''}`.trim()}</div> : null}
        {layoutId === 'classic-novel' ? <div className="page-preview__chapter-label">Chapter draft</div> : null}
        <div className={`page-content-frame ${editing ? 'is-editing' : ''}`}>
          {editing ? (
            <textarea className="page-text-flow" autoFocus value={draftText} onChange={(e) => setDraftText(e.target.value)} onBlur={() => void saveIfChanged()} onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') void saveIfChanged()
              if (e.key === 'Escape') { setDraftText(text); setEditing(false) }
            }} />
          ) : (
            <article className="page-text-flow" title={canEdit ? 'Double-click to edit text' : undefined} onDoubleClick={() => canEdit && setEditing(true)} style={canEdit ? { cursor: 'text' } : undefined}>{visibleText}</article>
          )}
          {truncated && !editing ? <><div className="page-overflow-fade" /><p className="continues-marker">Continues on next page</p></> : null}
        </div>
        {layoutId === 'modern-editorial' ? <aside className="page-preview__callout">Pull quote / callout space</aside> : null}
      </div>
    </div>
  )
}
