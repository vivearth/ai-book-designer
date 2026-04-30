import { useEffect, useState } from 'react'
import { resolveUploadUrl } from '../api'
import type { Book, Page } from '../types'
import { estimatePageCapacity } from '../utils/pageCapacity'

type LayoutElement = { id: string; type: string; role?: string; image_id?: string; caption_element_id?: string; text?: string; text_source?: string; box: { x: number; y: number; w: number; h: number }; z?: number; fit?: string }


function resolveElementText(el: LayoutElement, page: Page | null, bodyText: string): string {
  const direct = typeof el.text === 'string' ? el.text : ''
  if (direct.trim()) return direct
  const role = (el.role || '').toLowerCase()
  if (role === 'page_label') return page ? `PAGE ${page.page_number}` : ''
  const source = (el.text_source || '').toLowerCase()
  if (source === 'final_text') return page?.final_text || ''
  if (source === 'generated_text') return page?.generated_text || ''
  if (source === 'user_text') return page?.user_text || ''
  if (role === 'body' || el.id === 'text_main') return bodyText
  return ''
}

function getEffectiveCapacity(book: Book, page: Page | null, activeLayout: Record<string, any>) {
  const md = (page?.generation_metadata || {}) as Record<string, any>
  const pagination = (md.pagination || {}) as Record<string, any>
  if (typeof pagination.estimated_capacity_words === 'number') return pagination.estimated_capacity_words
  if (typeof activeLayout?.validation?.estimated_text_capacity_words === 'number') return activeLayout.validation.estimated_text_capacity_words
  return estimatePageCapacity(book, page).estimated_words
}

export function PagePreview({ book, page, layoutOverride, mini = false, editable = false, onTextSave, onImageSelect }: { book: Book; page: Page | null; layoutOverride?: Record<string, unknown> | null; mini?: boolean; editable?: boolean; onTextSave?: (nextText: string) => Promise<void> | void; onImageSelect?: (imageId: string) => void }) {
  const activeLayout = (layoutOverride || page?.layout_json || {}) as Record<string, any>
  const hasSchemaElements = activeLayout?.layout_schema === "page-layout-1" && Array.isArray(activeLayout?.elements) && activeLayout.elements.length > 0
  if (!hasSchemaElements) return <div className="page-preview"><div className="page-preview__body"><div className="page-content-frame" style={{ display: "grid", placeItems: "center", minHeight: mini ? "180px" : "420px" }}><p className="muted" style={{ textAlign: "center", margin: 0 }}>Page layout missing. Regenerate layout.</p></div></div></div>

  const text = page?.final_text || page?.generated_text || page?.user_text || ''
  const canEdit = editable && !mini
  const [editingElementId, setEditingElementId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [draftText, setDraftText] = useState(text)
  useEffect(() => setDraftText(text), [text, page?.id])

  const capacity = getEffectiveCapacity(book, page, activeLayout)
  const words = text.trim().split(/\s+/)
  const clipped = words.length > (capacity + 20)
  const visibleText = clipped ? `${words.slice(0, capacity).join(' ')}…` : text
  const pagination = ((page?.generation_metadata || {}) as Record<string, any>).pagination as Record<string, any> | undefined
  const continues = Boolean(pagination?.overflow_words > 0 || (page?.generation_metadata as any)?.continued_to_page_id || clipped)

  async function saveIfChanged() { if (saving) return; if (draftText === text) return setEditingElementId(null); setSaving(true); try { await onTextSave?.(draftText); setEditingElementId(null) } finally { setSaving(false) } }

  const pageDef = activeLayout.page
  const elements: LayoutElement[] = activeLayout.elements
  const pageImages = new Map((page?.images || []).map((img) => [img.id, img]))
  const imageForCaption = (el: LayoutElement) => { const owner = elements.find((i) => i.type === 'image' && i.caption_element_id === el.id); return owner?.image_id ? pageImages.get(owner.image_id) || null : null }

  return <div className={`page-preview ${mini ? 'page-preview--mini' : ''}`}><div className="page-preview__meta" aria-label="editor-chrome-page-meta">{page ? `Page ${page.page_number}` : 'Preview page'}</div><div className="page-preview__body"><div className="page-content-frame"><div className="page-preview-canvas" style={{ aspectRatio: `${pageDef.width}/${pageDef.height}` }}>{elements.map((el) => { const st = { left: `${(el.box.x / pageDef.width) * 100}%`, top: `${(el.box.y / pageDef.height) * 100}%`, width: `${(el.box.w / pageDef.width) * 100}%`, height: `${(el.box.h / pageDef.height) * 100}%`, zIndex: el.z || (el.type === 'image' ? 10 : 20) }
    if (el.type === 'image') { const img = el.image_id ? pageImages.get(el.image_id) : undefined; if (!img) return null; return <img key={el.id} className="page-preview-element page-preview-element--image" src={resolveUploadUrl(img.stored_filename)} alt={img.original_filename} style={{ ...st, objectFit: (el.fit || 'contain') as any }} onDoubleClick={() => !mini && onImageSelect?.(img.id)} /> }
    if (el.type === 'text') { const elementText = resolveElementText(el, page, visibleText); const isBodyText = (el.role || '').toLowerCase() === 'body' || el.id === 'text_main'; const isEditing = isBodyText && editingElementId === el.id && canEdit; return isEditing ? <textarea key={el.id} className="page-preview-element page-preview-element--text page-preview-element--editing" autoFocus value={draftText} onChange={(e) => setDraftText(e.target.value)} style={st} onBlur={() => void saveIfChanged()} onKeyDown={(e) => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); void saveIfChanged() } if (e.key === 'Escape') { setDraftText(text); setEditingElementId(null) } }} /> : <div key={el.id} className="page-preview-element page-preview-element--text" style={st} onDoubleClick={() => isBodyText && canEdit && setEditingElementId(el.id)}>{elementText}</div> }
    if (el.type === 'caption') { const captionText = (typeof el.text === 'string' && el.text.trim()) || imageForCaption(el)?.caption || (!mini ? 'Caption' : ''); return <div key={el.id} className="page-preview-element page-preview-element--caption" style={st}>{captionText}</div> }
    return null
  })}</div>{continues ? <p className="continues-marker">Continues on next page</p> : null}</div></div></div>
}
