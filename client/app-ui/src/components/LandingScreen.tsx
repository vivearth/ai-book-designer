import { useEffect, useMemo, useState } from 'react'
import type { Book } from '../types'

function toTimestamp(book: Book) {
  return new Date(book.updated_at || book.created_at || 0).getTime()
}

export function LandingScreen({ books, onContinue, onStartNew }: { books: Book[]; onContinue: (book: Book) => void; onStartNew: () => void; revealProjects: boolean; setRevealProjects: (value: boolean) => void }) {
  const sortedBooks = useMemo(() => [...books].sort((a, b) => toTimestamp(b) - toTimestamp(a)), [books])
  const [selectedResumeBookId, setSelectedResumeBookId] = useState('')

  useEffect(() => {
    setSelectedResumeBookId(sortedBooks[0]?.id ?? '')
  }, [sortedBooks])

  const selectedBook = sortedBooks.find((book) => book.id === selectedResumeBookId) || sortedBooks[0]

  return (
    <section className="landing-shell landing-shell--immersive">
      <div className="landing-bg-effects" aria-hidden="true" />

      <header className="landing-topbar">
        <div className="landing-brand">
          <div className="landing-logo-mark" aria-hidden="true">✦</div>
          <div>
            <h2>Lumina Book Studio</h2>
            <p>AI-powered book creation and typesetting</p>
          </div>
        </div>
        <button type="button" className="ghost-button landing-signin" disabled>👤 Sign in</button>
      </header>

      <main className="landing-hero">
        <h1 className="landing-title">
          Imagine it.<br />
          We design it.<br />
          You <span className="gradient-text">publish it.</span>
        </h1>
        <p>AI-powered layouts, beautiful pages, and a live book preview — from rough content to print-ready draft.</p>

        <div className="landing-action-row">
          <article className="glass-card landing-cta-card">
            {!sortedBooks.length ? (
              <>
                <h3>Start designing your book</h3>
                <p>Create a new book from a title, idea, notes, or source files.</p>
                <button type="button" className="premium-button" onClick={onStartNew}>Start designing your book</button>
              </>
            ) : (
              <>
                <div className="landing-card-header">
                  <div className="landing-card-icon" aria-hidden="true">📘</div>
                  <div>
                    <h3>Continue your work</h3>
                    <p>Pick up where you left off.</p>
                  </div>
                </div>
                <label className="ui-field">
                  <span>Saved books</span>
                  <select value={selectedBook?.id || ''} onChange={(event) => setSelectedResumeBookId(event.target.value)}>
                    {sortedBooks.map((book) => (
                      <option key={book.id} value={book.id}>
                        {book.title} · {new Date(book.updated_at || book.created_at || '').toLocaleDateString()}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="landing-cta-actions">
                  <button type="button" className="premium-button" onClick={() => selectedBook && onContinue(selectedBook)}>✦ Resume selected book</button>
                  <button type="button" className="ghost-button" onClick={onStartNew}>＋ Start a new book</button>
                </div>
              </>
            )}
          </article>

          <article className="landing-preview-card glass-card" aria-hidden="true">
            <div className="landing-book-visual">
              <span className="landing-book-spine" />
            </div>
            <h4>The Future of Work</h4>
            <p>Live visual preview of your designed pages.</p>
          </article>
        </div>

        <footer className="landing-feature-chips">
          <span>✦ AI-powered layouts</span>
          <span>𝑇 Beautiful typesetting</span>
          <span>📘 Export-ready books</span>
        </footer>
      </main>
    </section>
  )
}
