import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { api } from './api'
import './styles.css'
import type { Book, Page, Project } from './types'
import { LandingScreen } from './components/LandingScreen'
import { BookWorkspace } from './components/BookWorkspace'
import { BookCreationWizard } from './components/BookCreationWizard'

type UIMode = 'landing' | 'wizard' | 'workspace'

function App() {
  const [mode, setMode] = useState<UIMode>('landing')
  const [books, setBooks] = useState<Book[]>([])
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [pages, setPages] = useState<Page[]>([])
  const [projects, setProjects] = useState<Project[]>([])

  async function refreshBase() {
    setBooks(await api.listBooks())
    setProjects(await api.listProjects())
  }

  async function openBook(book: Book) {
    setSelectedBook(book)
    setPages(await api.listPages(book.id))
    setMode('workspace')
  }

  useEffect(() => { void refreshBase() }, [])

  return (
    <main className="app-shell">
      {mode === 'landing' ? (
        <LandingScreen books={books} onContinue={(book) => void openBook(book)} onStartNew={() => setMode('wizard')} revealProjects={true} setRevealProjects={() => {}} />
      ) : null}

      {mode === 'wizard' ? (
        <BookCreationWizard onCancel={() => setMode('landing')} onCreated={(book) => { void refreshBase(); void openBook(book) }} />
      ) : null}

      {mode === 'workspace' && selectedBook ? (
        <BookWorkspace
          book={selectedBook}
          pages={pages}
          setPages={setPages}
          refreshPages={async () => setPages(await api.listPages(selectedBook.id))}
          onBack={() => setMode('landing')}
          onSelectProject={(book) => void openBook(book)}
          books={books}
          project={projects.find((p) => p.id === selectedBook.project_id) || null}
        />
      ) : null}
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
