import { useEffect, useState } from 'react'
import { resolveUploadUrl } from '../api'
import type { Book, Page } from '../types'
import { estimatePageCapacity } from '../utils/pageCapacity'

type LayoutElement = { id: string; type: string; image_id?: string; caption_element_id?: string; text?: string; box: { x: number; y: number; w: number; h: number }; z?: number; fit?: string }

function InternalImagePlaceholder({ layoutId }: { layoutId: string }) {
  return <div className={`internal-image-placeholder internal-image-placeholder--${layoutId}`} />
}

export function PagePreview({ book, page, layoutOverride, mini = false, editable = false, onTextSave, onImageSelect }: { book: Book; page: Page | null; layoutOverride?: Record<string, unknown> | null; mini?: boolean; editable?: boolean; onTextSave?: (nextText: string) => Promise<void> | void; onImageSelect?: (imageId: string) => void }) {
  const layoutId = book.format_settings?.selected_layout_id || book.layout_template
  const activeLayout = (layoutOverride || page?.layout_json || {}) as Record<string, any>
  const hasSchemaElements = activeLayout?.schema_version === 2 && Array.isArray(activeLayout?.elements) && activeLayout.elements.length > 0
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
  const [editingElementId, setEditingElementId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [draftText, setDraftText] = useState(text)
  useEffect(() => setDraftText(text), [text, page?.id])

  async function saveIfChanged(close = true) {
    if (saving) return
    if (draftText === text) {
      if (close) setEditingElementId(null)
      return
    }
    setSaving(true)
    try {
      await onTextSave?.(draftText)
      if (close) setEditingElementId(null)
    } finally {
      setSaving(false)
    }
  }

  if (!hasSchemaElements) {
    const editing = Boolean(editingElementId)
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
                if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); void saveIfChanged() }
                if (e.key === 'Escape') { setDraftText(text); setEditingElementId(null) }
              }} />
            ) : (
              <article className="page-text-flow" title={canEdit ? 'Double-click to edit text' : undefined} onDoubleClick={() => canEdit && setEditingElementId('text_main')} style={canEdit ? { cursor: 'text' } : undefined}>{visibleText}</article>
            )}
            {truncated && !editing ? <><div className="page-overflow-fade" /><p className="continues-marker">Continues on next page</p></> : null}
          </div>
          {layoutId === 'modern-editorial' ? <aside className="page-preview__callout">Pull quote / callout space</aside> : null}
        </div>
      </div>
    )
  }

  const pageDef = activeLayout.page || { width: 595, height: 842, safe_area: { x: 36, y: 36, w: 523, h: 770 } }
  const elements: LayoutElement[] = activeLayout.elements
  const pageImages = new Map((page?.images || []).map((img) => [img.id, img]))
  const imageForCaption = (el: LayoutElement) => {
    const owner = elements.find((i) => i.type === 'image' && i.caption_element_id === el.id)
    if (!owner?.image_id) return null
    return pageImages.get(owner.image_id) || null
  }

  return (
    <div className={`page-preview page-preview--${layoutId} page-preview--${composition} ${mini ? 'page-preview--mini' : ''}`}>
      <div className="page-preview__meta">{page ? `Page ${page.page_number}` : 'Preview page'}</div>
      <div className="page-preview-canvas" style={{ position: 'relative', width: pageDef.width / (mini ? 4 : 1.8), aspectRatio: `${pageDef.width}/${pageDef.height}`, background: '#fff', border: '1px solid #ddd' }}>
        {elements.map((el) => {
          const style = { position: 'absolute' as const, left: `${(el.box.x / pageDef.width) * 100}%`, top: `${(el.box.y / pageDef.height) * 100}%`, width: `${(el.box.w / pageDef.width) * 100}%`, height: `${(el.box.h / pageDef.height) * 100}%`, zIndex: el.z || (el.type === 'image' ? 10 : 20), overflow: 'hidden' }
          if (el.type === 'image') {
            const img = el.image_id ? pageImages.get(el.image_id) : undefined
            if (!img) return null
            return <img key={el.id} src={resolveUploadUrl(img.stored_filename)} alt={img.original_filename} style={{ ...style, objectFit: (el.fit || 'contain') as any }} onDoubleClick={() => !mini && onImageSelect?.(img.id)} />
          }
          if (el.type === 'text') {
            const isEditing = editingElementId === el.id
            if (isEditing && canEdit) {
              return <textarea key={el.id} className="page-text-flow" autoFocus value={draftText} onChange={(e) => setDraftText(e.target.value)} style={{ ...style, fontSize: mini ? 7 : 12, lineHeight: 1.4, resize: 'none', background: 'rgba(255,255,255,0.95)' }} onBlur={() => void saveIfChanged()} onKeyDown={(e) => {
                if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); void saveIfChanged() }
                if (e.key === 'Escape') { setDraftText(text); setEditingElementId(null) }
              }} />
            }
            return <div key={el.id} style={{ ...style, fontSize: mini ? 7 : 12, lineHeight: 1.4, cursor: canEdit ? 'text' : undefined }} onDoubleClick={() => canEdit && setEditingElementId(el.id)}>{visibleText}</div>
          }
          if (el.type === 'caption') {
            const captionText = (typeof el.text === 'string' && el.text.trim()) || imageForCaption(el)?.caption || (!mini ? 'Caption' : '')
            return <div key={el.id} style={{ ...style, fontSize: mini ? 6 : 10, lineHeight: 1.3, color: '#555' }}>{captionText}</div>
          }
          return null
        })}
      </div>
    </div>
  )
}
