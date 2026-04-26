import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { api } from './api'
import type { Book, Page } from './types'
import './styles.css'

const emptyBook = {
  title: 'Untitled',
  topic: '',
  genre: 'Novel',
  tone: 'cinematic, simple, emotionally grounded',
  target_audience: 'general readers',
  writing_style: 'clear, visual prose with continuity across pages',
  page_size: 'A4',
  layout_template: 'classic',
}

function App() {
  const [books, setBooks] = useState<Book[]>([])
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [pages, setPages] = useState<Page[]>([])
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null)
  const [bookDraft, setBookDraft] = useState(emptyBook)
  const [pageDraft, setPageDraft] = useState({ page_number: 1, user_prompt: '', user_text: '' })
  const [generationInstruction, setGenerationInstruction] = useState('Polish and continue this page without breaking continuity.')
  const [lastContextPacket, setLastContextPacket] = useState<Record<string, unknown> | null>(null)
  const [continuityNotes, setContinuityNotes] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedPage = useMemo(() => pages.find((p) => p.id === selectedPageId) ?? pages[0] ?? null, [pages, selectedPageId])

  async function loadBooks() {
    const result = await api.listBooks()
    setBooks(result)
    if (!selectedBook && result[0]) setSelectedBook(result[0])
  }

  async function loadPages(bookId: string) {
    const result = await api.listPages(bookId)
    setPages(result)
    setSelectedPageId(result[0]?.id ?? null)
    setPageDraft((prev) => ({ ...prev, page_number: result.length + 1 }))
  }

  useEffect(() => {
    loadBooks().catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (selectedBook) {
      loadPages(selectedBook.id).catch((err) => setError(err.message))
    }
  }, [selectedBook?.id])

  async function guarded(action: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setBusy(false)
    }
  }

  async function createBook() {
    await guarded(async () => {
      const book = await api.createBook(bookDraft)
      setBooks([book, ...books])
      setSelectedBook(book)
    })
  }

  async function saveBook() {
    if (!selectedBook) return
    await guarded(async () => {
      const book = await api.updateBook(selectedBook.id, selectedBook)
      setSelectedBook(book)
      await loadBooks()
    })
  }

  async function createPage() {
    if (!selectedBook) return
    await guarded(async () => {
      const page = await api.createPage(selectedBook.id, pageDraft)
      await loadPages(selectedBook.id)
      setSelectedPageId(page.id)
      setPageDraft({ page_number: page.page_number + 1, user_prompt: '', user_text: '' })
    })
  }

  async function savePageText(page: Page) {
    await guarded(async () => {
      await api.updatePage(page.id, {
        user_prompt: page.user_prompt,
        user_text: page.user_text,
        final_text: page.final_text,
      })
      if (selectedBook) await loadPages(selectedBook.id)
    })
  }

  async function generatePage(page: Page) {
    await guarded(async () => {
      const result = await api.generatePage(page.id, {
        instruction: generationInstruction,
        target_words: 350,
        allow_new_characters: false,
      })
      setLastContextPacket(result.context_packet)
      setContinuityNotes(result.continuity_notes)
      if (selectedBook) await loadPages(selectedBook.id)
      setSelectedPageId(result.page.id)
    })
  }

  async function approvePage(page: Page) {
    await guarded(async () => {
      const result = await api.approvePage(page.id)
      if (selectedBook) await loadPages(selectedBook.id)
      setSelectedPageId(result.id)
    })
  }

  async function uploadImage(page: Page, file: File | null) {
    if (!file) return
    await guarded(async () => {
      await api.uploadImage(page.id, file, 'User supplied image for this page')
      if (selectedBook) await loadPages(selectedBook.id)
    })
  }

  async function exportPdf() {
    if (!selectedBook) return
    await guarded(async () => {
      const result = await api.exportPdf(selectedBook.id)
      window.open(result.download_url, '_blank')
    })
  }

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Rapid POC</p>
          <h1>AI Book Designer</h1>
          <p className="muted">Design a book page by page, maintain story memory, generate layouts, and export a PDF.</p>
        </div>
        <button disabled={!selectedBook || busy} onClick={exportPdf}>Export PDF</button>
      </header>

      {error && <div className="error">{error}</div>}
      {busy && <div className="notice">Working...</div>}

      <section className="grid three">
        <aside className="card">
          <h2>Create / Select Book</h2>
          <label>Title<input value={bookDraft.title} onChange={(e) => setBookDraft({ ...bookDraft, title: e.target.value })} /></label>
          <label>Topic<textarea value={bookDraft.topic} onChange={(e) => setBookDraft({ ...bookDraft, topic: e.target.value })} /></label>
          <label>Genre<input value={bookDraft.genre} onChange={(e) => setBookDraft({ ...bookDraft, genre: e.target.value })} /></label>
          <label>Tone<input value={bookDraft.tone} onChange={(e) => setBookDraft({ ...bookDraft, tone: e.target.value })} /></label>
          <button onClick={createBook} disabled={busy}>Create Book</button>
          <hr />
          <div className="list">
            {books.map((book) => (
              <button key={book.id} className={selectedBook?.id === book.id ? 'selected' : ''} onClick={() => setSelectedBook(book)}>
                {book.title}
              </button>
            ))}
          </div>
        </aside>

        <section className="card wide">
          <h2>Book Metadata</h2>
          {selectedBook ? (
            <div className="form-grid">
              <label>Title<input value={selectedBook.title} onChange={(e) => setSelectedBook({ ...selectedBook, title: e.target.value })} /></label>
              <label>Target Audience<input value={selectedBook.target_audience ?? ''} onChange={(e) => setSelectedBook({ ...selectedBook, target_audience: e.target.value })} /></label>
              <label>Writing Style<textarea value={selectedBook.writing_style ?? ''} onChange={(e) => setSelectedBook({ ...selectedBook, writing_style: e.target.value })} /></label>
              <label>Topic<textarea value={selectedBook.topic ?? ''} onChange={(e) => setSelectedBook({ ...selectedBook, topic: e.target.value })} /></label>
              <button onClick={saveBook} disabled={busy}>Save Book Metadata</button>
              <MemoryPanel book={selectedBook} />
            </div>
          ) : <p className="muted">Create or select a book.</p>}
        </section>
      </section>

      <section className="grid two">
        <aside className="card">
          <h2>Pages</h2>
          {selectedBook ? (
            <>
              <div className="page-list">
                {pages.map((page) => (
                  <button key={page.id} className={selectedPage?.id === page.id ? 'selected' : ''} onClick={() => setSelectedPageId(page.id)}>
                    Page {page.page_number} · {page.status}
                  </button>
                ))}
              </div>
              <hr />
              <h3>Add Page</h3>
              <label>Page Number<input type="number" value={pageDraft.page_number} onChange={(e) => setPageDraft({ ...pageDraft, page_number: Number(e.target.value) })} /></label>
              <label>Prompt<textarea value={pageDraft.user_prompt} onChange={(e) => setPageDraft({ ...pageDraft, user_prompt: e.target.value })} /></label>
              <label>Raw Text<textarea value={pageDraft.user_text} onChange={(e) => setPageDraft({ ...pageDraft, user_text: e.target.value })} /></label>
              <button onClick={createPage} disabled={busy}>Add Page</button>
            </>
          ) : <p className="muted">Select a book first.</p>}
        </aside>

        <section className="card editor">
          <h2>Page Editor</h2>
          {selectedPage ? (
            <PageEditor
              page={selectedPage}
              setPage={(updated) => setPages((existing) => existing.map((p) => p.id === updated.id ? updated : p))}
              savePageText={savePageText}
              generatePage={generatePage}
              approvePage={approvePage}
              uploadImage={uploadImage}
              generationInstruction={generationInstruction}
              setGenerationInstruction={setGenerationInstruction}
            />
          ) : <p className="muted">No page selected.</p>}
        </section>
      </section>

      <section className="grid two">
        <section className="card">
          <h2>Last Context Packet</h2>
          <pre>{lastContextPacket ? JSON.stringify(lastContextPacket, null, 2) : 'Generate a page to see the context packet.'}</pre>
        </section>
        <section className="card">
          <h2>Continuity Notes</h2>
          {continuityNotes.length ? <ul>{continuityNotes.map((note) => <li key={note}>{note}</li>)}</ul> : <p className="muted">No notes yet.</p>}
        </section>
      </section>
    </main>
  )
}

function MemoryPanel({ book }: { book: Book }) {
  return (
    <div className="memory">
      <h3>Book Memory</h3>
      <p><strong>Summary:</strong> {book.memory?.global_summary || 'No memory yet.'}</p>
      <p><strong>Characters:</strong> {book.memory?.characters?.length ?? 0}</p>
      <p><strong>Locations:</strong> {book.memory?.locations?.length ?? 0}</p>
      <p><strong>Timeline events:</strong> {book.memory?.timeline?.length ?? 0}</p>
    </div>
  )
}

function PageEditor({
  page,
  setPage,
  savePageText,
  generatePage,
  approvePage,
  uploadImage,
  generationInstruction,
  setGenerationInstruction,
}: {
  page: Page
  setPage: (page: Page) => void
  savePageText: (page: Page) => void
  generatePage: (page: Page) => void
  approvePage: (page: Page) => void
  uploadImage: (page: Page, file: File | null) => void
  generationInstruction: string
  setGenerationInstruction: (value: string) => void
}) {
  return (
    <div className="editor-grid">
      <div>
        <p className="badge">Page {page.page_number} · {page.status}</p>
        <label>User Prompt<textarea value={page.user_prompt ?? ''} onChange={(e) => setPage({ ...page, user_prompt: e.target.value })} /></label>
        <label>User Text<textarea value={page.user_text ?? ''} onChange={(e) => setPage({ ...page, user_text: e.target.value })} /></label>
        <label>Generation Instruction<textarea value={generationInstruction} onChange={(e) => setGenerationInstruction(e.target.value)} /></label>
        <label>Upload Image<input type="file" accept="image/*" onChange={(e) => uploadImage(page, e.target.files?.[0] ?? null)} /></label>
        <div className="actions">
          <button onClick={() => savePageText(page)}>Save Page</button>
          <button onClick={() => generatePage(page)}>Generate</button>
          <button onClick={() => approvePage(page)}>Approve</button>
        </div>
        <h3>Images</h3>
        {page.images.length ? page.images.map((img) => <p key={img.id}>{img.original_filename}</p>) : <p className="muted">No images uploaded.</p>}
      </div>
      <div className="preview">
        <h3>Generated / Final Preview</h3>
        <article>{page.final_text || page.generated_text || page.user_text || 'No page text yet.'}</article>
        <h3>Layout JSON</h3>
        <pre>{JSON.stringify(page.layout_json, null, 2)}</pre>
      </div>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
