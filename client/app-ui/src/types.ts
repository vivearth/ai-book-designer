export type PreviewScenario = { id: 'image-only' | 'text-with-image' | 'text-only'; title: string; description: string }

export type BookMemory = {
  global_summary: string
  characters: unknown[]
  locations: unknown[]
  timeline: unknown[]
  rules: unknown[]
  unresolved_threads: unknown[]
  style_guide: Record<string, unknown>
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

export type Project = {
  id: string
  name: string
  description?: string | null
  content_direction: string
  audience?: string | null
  objective?: string | null
  status: string
  created_at: string
  updated_at: string
}

export type SourceAsset = {
  id: string
  project_id: string
  title: string
  original_filename?: string | null
  stored_filename?: string | null
  content_type?: string | null
  source_type: string
  extracted_text?: string | null
  summary?: string | null
  tags: string[]
  asset_metadata: Record<string, unknown>
  status: string
  created_at: string
  updated_at: string
}

export type SourceChunk = {
  id: string
  source_asset_id: string
  project_id: string
  chunk_index: number
  text: string
  summary?: string | null
  token_estimate?: number | null
  metadata: Record<string, unknown>
  created_at: string
}

export type Book = {
  id: string
  project_id?: string | null
  book_type_id: string
  creation_mode: 'classical' | 'expert'
  objective?: string | null
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
  cover_source?: 'uploaded' | 'generated' | 'none' | null
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
  generation_metadata: Record<string, unknown>
  selected_layout_option_id?: string | null
  status: string
  created_at: string
  updated_at: string
  images: PageImage[]
}

export type PageLayoutOption = {
  id: string
  page_id: string
  option_index: number
  label: string
  layout_json: Record<string, unknown>
  preview_metadata: Record<string, unknown>
  rationale?: string | null
  created_at: string
  selected_at?: string | null
}

export type LayoutOptionsResponse = {
  page_id: string
  options: PageLayoutOption[]
  warnings: string[]
}

export type GenerationResponse = {
  page: Page
  context_packet: Record<string, unknown>
  continuity_notes: string[]
  skill_output?: Record<string, unknown>
  source_refs: { source_asset_id?: string; chunk_id?: string; reason?: string }[]
  quality_report?: { score: number; flags: Record<string, boolean>; issues: string[]; suggested_fixes: string[] }
  warnings: string[]
  overflow_created_page?: Page | null
  overflow_warning?: string | null
}


export type DraftGenerationResponse = {
  book_plan: Record<string, unknown>
  created_pages: Page[]
  warnings: string[]
  source_summary: Record<string, unknown>
}
