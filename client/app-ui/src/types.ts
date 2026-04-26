export type BookMemory = {
  global_summary: string
  characters: unknown[]
  locations: unknown[]
  timeline: unknown[]
  rules: unknown[]
  unresolved_threads: unknown[]
  style_guide: Record<string, unknown>
}

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
