import type { Book, GenerationResponse, Page, PageImage } from './types'

const API_BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: options?.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  listBooks: () => request<Book[]>('/books'),
  createBook: (payload: Partial<Book>) => request<Book>('/books', { method: 'POST', body: JSON.stringify(payload) }),
  updateBook: (bookId: string, payload: Partial<Book>) => request<Book>(`/books/${bookId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  listPages: (bookId: string) => request<Page[]>(`/books/${bookId}/pages`),
  createPage: (bookId: string, payload: { page_number: number; user_prompt?: string; user_text?: string }) =>
    request<Page>(`/books/${bookId}/pages`, { method: 'POST', body: JSON.stringify(payload) }),
  updatePage: (pageId: string, payload: Partial<Page>) =>
    request<Page>(`/pages/${pageId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  generatePage: (pageId: string, payload: { instruction?: string; target_words?: number; allow_new_characters?: boolean }) =>
    request<GenerationResponse>(`/pages/${pageId}/generate`, { method: 'POST', body: JSON.stringify(payload) }),
  approvePage: (pageId: string) => request<Page>(`/pages/${pageId}/approve`, { method: 'POST' }),
  uploadImage: (pageId: string, file: File, caption?: string) => {
    const body = new FormData()
    body.append('file', file)
    if (caption) body.append('caption', caption)
    return request<PageImage>(`/pages/${pageId}/images`, { method: 'POST', body })
  },
  exportPdf: (bookId: string) => request<{ book_id: string; filename: string; download_url: string }>(`/books/${bookId}/export/pdf`, { method: 'POST' }),
}
