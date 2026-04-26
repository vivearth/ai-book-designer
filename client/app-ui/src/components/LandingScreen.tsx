import type { Book } from '../types'
import { ProjectSwitcher } from './ProjectSwitcher'

export function LandingScreen({ books, onContinue, onStartNew, revealProjects, setRevealProjects }: { books: Book[]; onContinue: (book: Book) => void; onStartNew: () => void; revealProjects: boolean; setRevealProjects: (value: boolean) => void }) {
  return (
    <section className="landing-shell">
      <div className="landing-ambient-grid" />
      <div className="landing-ambient-glow" />
      <div className="landing-copy">
        <p className="kicker">Professional AI content-to-book studio</p>
        <h1>Design a book your way: page by page or source-first expert draft.</h1>
        <p>
          Write page by page, or upload source material and generate a professional draft before editing each page.
        </p>
        <div className="landing-actions">
          <button type="button" className="ghost-button" onClick={() => setRevealProjects(true)}>
            Continue a project
          </button>
          <button type="button" className="premium-button" onClick={onStartNew}>Start a new book</button>
        </div>
        {revealProjects ? (
          books.length ? (
            <div className="studio-shelf">
              <ProjectSwitcher books={books} onSelect={onContinue} />
            </div>
          ) : (
            <p className="empty-note">No saved books yet. Start a new one and your studio shelf will fill up.</p>
          )
        ) : null}
      </div>
      <div className="landing-visual">
        <div className="hero-annotation hero-annotation--format">Format</div>
        <div className="hero-annotation hero-annotation--memory">Memory</div>
        <div className="hero-annotation hero-annotation--preview">Preview</div>
        <div className="book-stack">
          <article className="stacked-book stacked-book--front">
            <div className="stacked-book__spine" />
            <div className="stacked-book__scan-line" />
            <div className="stacked-book__guide-lines" />
            <div className="stacked-book__page">
              <small>Your book will appear here</small>
              <h3>Page by page, with a live preview.</h3>
            </div>
          </article>
          <article className="stacked-book stacked-book--middle" />
          <article className="stacked-book stacked-book--back" />
        </div>
      </div>
    </section>
  )
}
