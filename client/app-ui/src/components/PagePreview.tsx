import { resolveUploadUrl } from '../api'
import type { Book, Page } from '../types'

type LayoutElement = { id: string; type: string; image_id?: string; box: { x: number; y: number; w: number; h: number }; z?: number; fit?: string }

export function PagePreview({ page, layoutOverride, mini = false }: { book: Book; page: Page | null; layoutOverride?: Record<string, unknown> | null; mini?: boolean; editable?: boolean; onTextSave?: (nextText: string) => Promise<void> | void; onImageSelect?: (imageId: string) => void }) {
  const activeLayout = (layoutOverride || page?.layout_json || {}) as Record<string, any>
  const pageDef = activeLayout.page || { width: 595, height: 842, safe_area: { x: 36, y: 36, w: 523, h: 770 } }
  const elements: LayoutElement[] = Array.isArray(activeLayout.elements) ? activeLayout.elements : []
  const text = page?.final_text || page?.generated_text || page?.user_text || 'Your next page will appear here.'
  const pageImages = new Map((page?.images || []).map((img) => [img.id, img]))

  return (
    <div className={`page-preview-canvas ${mini ? 'page-preview-canvas--mini' : ''}`} style={{ position: 'relative', width: pageDef.width / (mini ? 4 : 1.8), aspectRatio: `${pageDef.width}/${pageDef.height}`, background: '#fff', border: '1px solid #ddd' }}>
      {elements.map((el) => {
        const style = {
          position: 'absolute' as const,
          left: `${(el.box.x / pageDef.width) * 100}%`,
          top: `${(el.box.y / pageDef.height) * 100}%`,
          width: `${(el.box.w / pageDef.width) * 100}%`,
          height: `${(el.box.h / pageDef.height) * 100}%`,
          zIndex: el.z || (el.type === 'image' ? 10 : 20),
          overflow: 'hidden',
        }
        if (el.type === 'image') {
          const img = el.image_id ? pageImages.get(el.image_id) : undefined
          if (!img) return null
          return <img key={el.id} src={resolveUploadUrl(img.stored_filename)} style={{ ...style, objectFit: (el.fit || 'contain') as any }} />
        }
        if (el.type === 'text' || el.type === 'caption') {
          return <div key={el.id} style={{ ...style, fontSize: mini ? 7 : 12, lineHeight: 1.4 }}>{text}</div>
        }
        return null
      })}
    </div>
  )
}
