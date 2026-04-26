import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { api } from './api'
import './styles.css'
import type { Book, Page } from './types'
import { BookOnboarding } from './components/BookOnboarding'
import { BookWorkspace } from './components/BookWorkspace'
import { LandingScreen } from './components/LandingScreen'

type UIMode = 'landing' | 'selecting-existing-book' | 'onboarding' | 'workspace'

function App() {
  const [mode, setMode] = useState<UIMode>('landing')
  const [books, setBooks] = useState<Book[]>([])
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [pages, setPages] = useState<Page[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [revealProjects, setRevealProjects] = useState(false)

  async function guarded(action: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  async function loadBooks() {
    const result = await api.listBooks()
    setBooks(result)
    if (selectedBook) {
      const fresh = result.find((book) => book.id === selectedBook.id) || null
      setSelectedBook(fresh)
    }
  }

  async function loadPages(bookId: string) {
    const result = await api.listPages(bookId)
    setPages(result)
  }

  useEffect(() => {
    guarded(loadBooks)
  }, [])

  async function openWorkspace(book: Book) {
    await guarded(async () => {
      setSelectedBook(book)
      await loadPages(book.id)
      setMode('workspace')
    })
  }

  async function refreshSelectedBook() {
    if (!selectedBook) return
    const fresh = await api.getBook(selectedBook.id)
    setSelectedBook(fresh)
    await loadBooks()
  }

  async function refreshPages() {
    if (!selectedBook) return
    await loadPages(selectedBook.id)
  }

  return (
    <main className="app-shell">
      {error ? <div className="error-banner global-error">{error}</div> : null}
      {busy && mode === 'landing' ? <div className="notice-pill">Loading your studio…</div> : null}

      {mode === 'landing' || mode === 'selecting-existing-book' ? (
        <LandingScreen
          books={books}
          onContinue={(book) => {
            setMode('selecting-existing-book')
            void openWorkspace(book)
          }}
          onStartNew={() => setMode('onboarding')}
          revealProjects={revealProjects}
          setRevealProjects={(value) => {
            setRevealProjects(value)
            setMode(value ? 'selecting-existing-book' : 'landing')
          }}
        />
      ) : null}

      {mode === 'onboarding' ? <BookOnboarding onCreated={(book) => { void loadBooks(); void openWorkspace(book) }} /> : null}

      {mode === 'workspace' && selectedBook ? (
        <BookWorkspace
          book={selectedBook}
          pages={pages}
          setPages={setPages}
          refreshBook={refreshSelectedBook}
          refreshPages={refreshPages}
          onBack={() => setMode('landing')}
          onSelectProject={(book) => void openWorkspace(book)}
          books={books}
        />
      ) : null}
    </main>
  )
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
