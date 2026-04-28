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
    <section className="landing-shell flow-background">
      <div className="gradient-orb gradient-orb--one" />
      <div className="gradient-orb gradient-orb--two" />
      <div className="gradient-orb gradient-orb--three" />

      <header className="landing-brand-row">
        <div>
          <h2>Book Designer AI</h2>
          <p>Design beautiful books in minutes.</p>
        </div>
        <button type="button" className="ghost-button" disabled>Sign in</button>
      </header>

      <div className="landing-hero-copy">
        <h1>
          Imagine it.<br />
          We design it.<br />
          You <span className="gradient-text">publish it.</span>
        </h1>
        <p>AI-powered layouts, beautiful pages, and a live book preview — from rough content to print-ready draft.</p>
      </div>

      <article className="glass-card landing-cta-card">
        {!sortedBooks.length ? (
          <>
            <h3>Start designing your book</h3>
            <p>Create a new book from a title, idea, notes, or source files.</p>
            <button type="button" className="premium-button" onClick={onStartNew}>Start designing your book</button>
          </>
        ) : (
          <>
            <h3>Resume work</h3>
            <p>Pick a saved book and continue where you left off.</p>
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
              <button type="button" className="premium-button" onClick={() => selectedBook && onContinue(selectedBook)}>Resume selected book</button>
              <button type="button" className="ghost-button" onClick={onStartNew}>Start a new book</button>
            </div>
          </>
        )}
      </article>


      <div className="landing-art-preview glass-card" aria-hidden="true">
        <div className="landing-art-preview__sheet">
          <h4>The Future of Work</h4>
          <p>Live visual preview of your designed pages.</p>
        </div>
      </div>

      <footer className="landing-feature-chips">
        <span>✦ AI-powered layouts</span>
        <span>◌ Beautiful typesetting</span>
        <span>⬢ Export-ready book</span>
      </footer>
    </section>
  )
}
