import { useEffect, useMemo, useState } from 'react'
import { resolveUploadUrl } from '../api'
import type { Book, Page } from '../types'
import { estimatePageCapacity } from '../utils/pageCapacity'

type LayoutElement = { id: string; type: string; image_id?: string; caption_element_id?: string; text?: string; box: { x: number; y: number; w: number; h: number }; z?: number; fit?: string }

function InternalImagePlaceholder({ layoutId }: { layoutId: string }) { return <div className={`internal-image-placeholder internal-image-placeholder--${layoutId}`} /> }

function getEffectiveCapacity(book: Book, page: Page | null, activeLayout: Record<string, any>, isSchemaV2: boolean) {
  if (isSchemaV2) {
    const md = (page?.generation_metadata || {}) as Record<string, any>
    const pagination = (md.pagination || {}) as Record<string, any>
    if (typeof pagination.estimated_capacity_words === 'number') return pagination.estimated_capacity_words
    if (typeof activeLayout?.validation?.estimated_text_capacity_words === 'number') return activeLayout.validation.estimated_text_capacity_words
  }
  return estimatePageCapacity(book, page).estimated_words
}

export function PagePreview({ book, page, layoutOverride, mini = false, editable = false, onTextSave, onImageSelect }: { book: Book; page: Page | null; layoutOverride?: Record<string, unknown> | null; mini?: boolean; editable?: boolean; onTextSave?: (nextText: string) => Promise<void> | void; onImageSelect?: (imageId: string) => void }) {
  const layoutId = book.format_settings?.selected_layout_id || book.layout_template
  const activeLayout = (layoutOverride || page?.layout_json || {}) as Record<string, any>
  const hasSchemaElements = activeLayout?.schema_version === 2 && Array.isArray(activeLayout?.elements) && activeLayout.elements.length > 0
  const text = page?.final_text || page?.generated_text || page?.user_text || 'Your next page will appear here as soon as you start shaping it.'
  const canEdit = editable && !mini
  const [editingElementId, setEditingElementId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [draftText, setDraftText] = useState(text)
  useEffect(() => setDraftText(text), [text, page?.id])

  const capacity = getEffectiveCapacity(book, page, activeLayout, hasSchemaElements)
  const words = text.trim().split(/\s+/)
  const clipped = words.length > (capacity + (hasSchemaElements ? 20 : 0))
  const visibleText = clipped ? `${words.slice(0, capacity).join(' ')}…` : text
  const pagination = ((page?.generation_metadata || {}) as Record<string, any>).pagination as Record<string, any> | undefined
  const continues = Boolean(pagination?.overflow_words > 0 || (page?.generation_metadata as any)?.continued_to_page_id || clipped)

  async function saveIfChanged() { if (saving) return; if (draftText === text) return setEditingElementId(null); setSaving(true); try { await onTextSave?.(draftText); setEditingElementId(null) } finally { setSaving(false) } }

  if (!hasSchemaElements) {
    const composition = (activeLayout?.composition as string | undefined) || (page?.images?.length ? 'text-with-image' : 'text_only')
    const image = page?.images?.[0]
    const headline = typeof page?.generation_metadata?.headline === 'string' ? String(page.generation_metadata.headline).trim() : null
    const showImageArea = composition !== 'text_only'
    const editing = Boolean(editingElementId)
    return <div className={`page-preview page-preview--${layoutId} page-preview--${composition} ${mini ? 'page-preview--mini' : ''}`}><div className="page-preview__meta">{page ? `Page ${page.page_number}` : 'Preview page'}</div>{showImageArea ? (image ? <img src={resolveUploadUrl(image.stored_filename)} alt={image.original_filename} className="page-preview__image" onDoubleClick={() => onImageSelect?.(image.id)} /> : <InternalImagePlaceholder layoutId={layoutId} />) : null}<div className="page-preview__body">{layoutId === 'modern-editorial' ? <div className="page-preview__headline">{headline || `Page ${page?.page_number || ''}`.trim()}</div> : null}{layoutId === 'classic-novel' ? <div className="page-preview__chapter-label">Chapter draft</div> : null}<div className={`page-content-frame ${editing ? 'is-editing' : ''}`}>{editing ? <textarea className="page-text-flow" autoFocus value={draftText} onChange={(e) => setDraftText(e.target.value)} onBlur={() => void saveIfChanged()} onKeyDown={(e) => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); void saveIfChanged() } if (e.key === 'Escape') { setDraftText(text); setEditingElementId(null) } }} /> : <article className="page-text-flow" title={canEdit ? 'Double-click to edit text' : undefined} onDoubleClick={() => canEdit && setEditingElementId('text_main')} style={canEdit ? { cursor: 'text' } : undefined}>{visibleText}</article>}{continues && !editing ? <><div className="page-overflow-fade" /><p className="continues-marker">Continues on next page</p></> : null}</div>{layoutId === 'modern-editorial' ? <aside className="page-preview__callout">Pull quote / callout space</aside> : null}</div></div>
  }

  const pageDef = activeLayout.page || { width: 595, height: 842, safe_area: { x: 36, y: 36, w: 523, h: 770 } }
  const elements: LayoutElement[] = activeLayout.elements
  const pageImages = new Map((page?.images || []).map((img) => [img.id, img]))
  const imageForCaption = (el: LayoutElement) => { const owner = elements.find((i) => i.type === 'image' && i.caption_element_id === el.id); return owner?.image_id ? pageImages.get(owner.image_id) || null : null }

  return <div className={`page-preview page-preview--${layoutId} page-preview--${activeLayout?.composition || 'text_only'} ${mini ? 'page-preview--mini' : ''}`}><div className="page-preview__meta">{page ? `Page ${page.page_number}` : 'Preview page'}</div><div className="page-preview__body"><div className="page-content-frame"><div className="page-preview-canvas" style={{ aspectRatio: `${pageDef.width}/${pageDef.height}` }}>{elements.map((el) => { const st = { left: `${(el.box.x / pageDef.width) * 100}%`, top: `${(el.box.y / pageDef.height) * 100}%`, width: `${(el.box.w / pageDef.width) * 100}%`, height: `${(el.box.h / pageDef.height) * 100}%`, zIndex: el.z || (el.type === 'image' ? 10 : 20) }
    if (el.type === 'image') { const img = el.image_id ? pageImages.get(el.image_id) : undefined; if (!img) return null; return <img key={el.id} className="page-preview-element page-preview-element--image" src={resolveUploadUrl(img.stored_filename)} alt={img.original_filename} style={{ ...st, objectFit: (el.fit || 'contain') as any }} onDoubleClick={() => !mini && onImageSelect?.(img.id)} /> }
    if (el.type === 'text') { const isEditing = editingElementId === el.id && canEdit; return isEditing ? <textarea key={el.id} className="page-preview-element page-preview-element--text page-preview-element--editing" autoFocus value={draftText} onChange={(e) => setDraftText(e.target.value)} style={st} onBlur={() => void saveIfChanged()} onKeyDown={(e) => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); void saveIfChanged() } if (e.key === 'Escape') { setDraftText(text); setEditingElementId(null) } }} /> : <div key={el.id} className="page-preview-element page-preview-element--text" style={st} onDoubleClick={() => canEdit && setEditingElementId(el.id)}>{visibleText}</div> }
    if (el.type === 'caption') { const captionText = (typeof el.text === 'string' && el.text.trim()) || imageForCaption(el)?.caption || (!mini ? 'Caption' : ''); return <div key={el.id} className="page-preview-element page-preview-element--caption" style={st}>{captionText}</div> }
    return null
  })}</div>{continues ? <p className="continues-marker">Continues on next page</p> : null}</div></div></div>
}
