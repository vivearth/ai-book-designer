export type BookMemory = {
  global_summary: string
  characters: unknown[]
  locations: unknown[]
  timeline: unknown[]
  rules: unknown[]
  unresolved_threads: unknown[]
  style_guide: Record<string, unknown>
}

export type PreviewScenario = {
  id: 'image-only' | 'text-with-image' | 'text-only'
  title: string
  description: string
}

export type FormatSettings = {
  selected_layout_id: 'classic-novel' | 'illustrated-story' | 'modern-editorial'
  layout_name: string
  page_size: string
  margin_style: string
  typography_style: string
  image_policy: string
  preview_scenarios: PreviewScenario[]
}

export type CoverSource = 'uploaded' | 'generated' | 'none'

export type Book = {
  id: string
  title: string
  topic?: string | null
  genre?: string | null
  tone?: string | null
  target_audience?: string | null
  writing_style?: string | null
  page_size: string
  layout_template: string
  status: string
  created_at: string
  updated_at: string
  memory?: BookMemory | null
  format_settings?: FormatSettings | null
  cover_image_filename?: string | null
  cover_original_filename?: string | null
  cover_content_type?: string | null
  cover_source?: CoverSource | null
}

export type PageImage = {
  id: string
  original_filename: string
  stored_filename: string
  content_type?: string | null
  caption?: string | null
  created_at: string
}

export type Page = {
  id: string
  book_id: string
  page_number: number
  user_prompt?: string | null
  user_text?: string | null
  generated_text?: string | null
  final_text?: string | null
  layout_json: Record<string, unknown>
  status: string
  created_at: string
  updated_at: string
  images: PageImage[]
}

export type GenerationResponse = {
  page: Page
  context_packet: Record<string, unknown>
  continuity_notes: string[]
}
