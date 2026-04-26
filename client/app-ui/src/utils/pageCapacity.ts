import type { Book, Page } from '../types'

export type PageCapacityHint = {
  visible_text_area_width_px: number
  visible_text_area_height_px: number
  font_family: string
  font_size_px: number
  line_height_px: number
  estimated_chars_per_line: number
  estimated_lines: number
  estimated_words: number
  composition: string
}

const CAPACITY_TABLE: Record<string, Record<string, [number, number]>> = {
  'classic-novel': {
    text_only: [280, 380],
    text_with_image: [120, 220],
    hero_image_with_text: [120, 220],
    image_grid_with_text: [20, 60],
  },
  'illustrated-story': {
    text_only: [120, 220],
    text_with_image: [60, 140],
    hero_image_with_text: [60, 140],
    image_grid_with_text: [10, 40],
  },
  'modern-editorial': {
    text_only: [220, 320],
    text_with_image: [100, 200],
    hero_image_with_text: [100, 200],
    image_grid_with_text: [20, 60],
  },
}

function midpoint(range: [number, number]) {
  return Math.round((range[0] + range[1]) / 2)
}

export function estimatePageCapacity(book: Book, page: Page | null): PageCapacityHint {
  const layout = book.format_settings?.selected_layout_id || book.layout_template || 'classic-novel'
  const composition = String(page?.layout_json?.composition || (page?.images?.length ? 'text_with_image' : 'text_only'))
  const typography = layout === 'illustrated-story'
    ? { font_family: 'Georgia', font_size_px: 15, line_height_px: 24 }
    : layout === 'modern-editorial'
      ? { font_family: 'Inter', font_size_px: 15, line_height_px: 22 }
      : { font_family: 'Georgia', font_size_px: 16, line_height_px: 28 }

  const frame = composition === 'text_only'
    ? { w: 470, h: 600 }
    : composition === 'text_with_image' || composition === 'hero_image_with_text'
      ? { w: 460, h: 360 }
      : { w: 430, h: 140 }

  const lines = Math.max(4, Math.floor(frame.h / typography.line_height_px))
  const charsPerLine = Math.max(18, Math.floor(frame.w / (typography.font_size_px * 0.55)))
  const heuristicWords = Math.round((lines * charsPerLine) / 5.4)
  const range = CAPACITY_TABLE[layout]?.[composition] || CAPACITY_TABLE[layout]?.text_only || [220, 320]
  const estimated_words = Math.max(range[0], Math.min(range[1], heuristicWords || midpoint(range)))

  return {
    visible_text_area_width_px: frame.w,
    visible_text_area_height_px: frame.h,
    font_family: typography.font_family,
    font_size_px: typography.font_size_px,
    line_height_px: typography.line_height_px,
    estimated_chars_per_line: charsPerLine,
    estimated_lines: lines,
    estimated_words,
    composition,
  }
}
