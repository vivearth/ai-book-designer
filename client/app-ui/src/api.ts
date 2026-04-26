import type { Book, GenerationResponse, Page, PageImage, Project, SourceAsset, SourceChunk } from './types'

const API_BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: options?.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error((await res.text()) || `Request failed: ${res.status}`)
  if (res.status === 204) return {} as T
  return res.json() as Promise<T>
}

export const api = {
  listBooks: () => request<Book[]>('/books'),
  getBook: (bookId: string) => request<Book>(`/books/${bookId}`),
  createBook: (payload: Partial<Book>) => request<Book>('/books', { method: 'POST', body: JSON.stringify(payload) }),
  updateBook: (bookId: string, payload: Partial<Book>) => request<Book>(`/books/${bookId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  uploadCover: (bookId: string, file: File) => {
    const body = new FormData(); body.append('file', file)
    return request<Book>(`/books/${bookId}/cover`, { method: 'POST', body })
  },
  listPages: (bookId: string) => request<Page[]>(`/books/${bookId}/pages`),
  createPage: (bookId: string, payload: { page_number: number; user_prompt?: string; user_text?: string }) =>
    request<Page>(`/books/${bookId}/pages`, { method: 'POST', body: JSON.stringify(payload) }),
  updatePage: (pageId: string, payload: Partial<Page>) => request<Page>(`/pages/${pageId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  generatePage: (pageId: string, payload: Record<string, unknown>) =>
    request<GenerationResponse>(`/pages/${pageId}/generate`, { method: 'POST', body: JSON.stringify(payload) }),
  approvePage: (pageId: string) => request<Page>(`/pages/${pageId}/approve`, { method: 'POST' }),
  uploadImage: (pageId: string, file: File, caption?: string) => {
    const body = new FormData(); body.append('file', file); if (caption) body.append('caption', caption)
    return request<PageImage>(`/pages/${pageId}/images`, { method: 'POST', body })
  },
  exportPdf: (bookId: string) => request<{ book_id: string; filename: string; download_url: string }>(`/books/${bookId}/export/pdf`, { method: 'POST' }),

  listProjects: () => request<Project[]>('/projects'),
  createProject: (payload: Partial<Project>) => request<Project>('/projects', { method: 'POST', body: JSON.stringify(payload) }),
  getProject: (projectId: string) => request<Project>(`/projects/${projectId}`),
  listProjectBooks: (projectId: string) => request<Book[]>(`/projects/${projectId}/books`),
  createProjectBook: (projectId: string, payload: Partial<Book>) => request<Book>(`/projects/${projectId}/books`, { method: 'POST', body: JSON.stringify(payload) }),

  listSources: (projectId: string) => request<SourceAsset[]>(`/projects/${projectId}/sources`),
  createTextSource: (projectId: string, payload: { title?: string; text: string; source_type?: string; tags?: string[] }) =>
    request<SourceAsset>(`/projects/${projectId}/sources/text`, { method: 'POST', body: JSON.stringify(payload) }),
  uploadSource: (projectId: string, file: File, extra?: { title?: string; source_type?: string; tags?: string }) => {
    const body = new FormData(); body.append('file', file)
    if (extra?.title) body.append('title', extra.title)
    if (extra?.source_type) body.append('source_type', extra.source_type)
    if (extra?.tags) body.append('tags', extra.tags)
    return request<SourceAsset>(`/projects/${projectId}/sources`, { method: 'POST', body })
  },
  processSource: (sourceId: string) => request<SourceAsset>(`/sources/${sourceId}/process`, { method: 'POST' }),
  deleteSource: (sourceId: string) => request<{ deleted: boolean }>(`/sources/${sourceId}`, { method: 'DELETE' }),
  queryChunks: (projectId: string, query?: string) => request<SourceChunk[]>(`/projects/${projectId}/source-chunks${query ? `?query=${encodeURIComponent(query)}` : ''}`),
}

export const resolveUploadUrl = (filename: string) => `${API_BASE}/uploads/${filename}`
export const resolveGeneratedCoverUrl = (bookId: string) => `${API_BASE}/books/${bookId}/cover/generated.svg`
