import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { api } from './api'
import './styles.css'
import type { Book, Project } from './types'
import { LandingScreen } from './components/LandingScreen'
import { BookOnboarding } from './components/BookOnboarding'
import { BookWorkspace } from './components/BookWorkspace'
import { ProjectOnboarding } from './components/ProjectOnboarding'
import { ProfessionalWorkspace } from './components/ProfessionalWorkspace'

type UIMode = 'landing' | 'onboarding' | 'workspace' | 'project-onboarding' | 'project-workspace'

function App() {
  const [mode, setMode] = useState<UIMode>('landing')
  const [books, setBooks] = useState<Book[]>([])
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [pages, setPages] = useState<any[]>([])
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [projects, setProjects] = useState<Project[]>([])

  async function refreshBase() {
    setBooks(await api.listBooks())
    setProjects(await api.listProjects())
  }

  useEffect(() => { void refreshBase() }, [])

  return (
    <main className="app-shell">
      {mode === 'landing' ? (
        <div>
          <LandingScreen books={books} onContinue={(book) => { setSelectedBook(book); setMode('workspace') }} onStartNew={() => setMode('onboarding')} revealProjects={true} setRevealProjects={() => {}} />
          <section className="panel">
            <h2>Professional project studio</h2>
            <p>Turn curated business content into a polished book. Upload reports, campaign notes, decks, and source material for grounded generation.</p>
            <button onClick={() => setMode('project-onboarding')}>Start a professional book project</button>
            <div className="list-col">{projects.map((p) => <button key={p.id} onClick={() => { setSelectedProject(p); setMode('project-workspace') }}>Open: {p.name}</button>)}</div>
          </section>
        </div>
      ) : null}

      {mode === 'project-onboarding' ? <ProjectOnboarding onCreated={(project) => { setSelectedProject(project); void refreshBase(); setMode('project-workspace') }} /> : null}
      {mode === 'project-workspace' && selectedProject ? <ProfessionalWorkspace project={selectedProject} onBack={() => setMode('landing')} /> : null}

      {mode === 'onboarding' ? <BookOnboarding onCreated={(book) => { setSelectedBook(book); void refreshBase(); setMode('workspace') }} /> : null}
      {mode === 'workspace' && selectedBook ? (
        <BookWorkspace book={selectedBook} pages={pages} setPages={setPages} refreshBook={async () => setSelectedBook(await api.getBook(selectedBook.id))} refreshPages={async () => setPages(await api.listPages(selectedBook.id))} onBack={() => setMode('landing')} onSelectProject={(book) => setSelectedBook(book)} books={books} />
      ) : null}
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
