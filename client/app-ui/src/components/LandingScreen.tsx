import type { Book } from '../types'
import { ProjectSwitcher } from './ProjectSwitcher'

export function LandingScreen({ books, onContinue, onStartNew, revealProjects, setRevealProjects }: { books: Book[]; onContinue: (book: Book) => void; onStartNew: () => void; revealProjects: boolean; setRevealProjects: (value: boolean) => void }) {
  return (
    <section className="landing-shell">
      <div className="landing-copy">
        <p className="kicker">AI-assisted book design studio</p>
        <h1>Design your book before you write all of it.</h1>
        <p>
          Start with a title, a direction, and a format. Then shape every page with an assistant that remembers the book you are building.
        </p>
        <div className="landing-actions">
          <button type="button" className="ghost-button" onClick={() => setRevealProjects(true)}>
            Continue working on your books
          </button>
          <button type="button" onClick={onStartNew}>Write a new book</button>
        </div>
        {revealProjects ? (
          books.length ? (
            <ProjectSwitcher books={books} onSelect={onContinue} />
          ) : (
            <p className="empty-note">No saved books yet. Start a new one and your studio shelf will fill up.</p>
          )
        ) : null}
      </div>
      <div className="landing-visual">
        <div className="book-stack">
          <article className="stacked-book stacked-book--front">
            <div className="stacked-book__spine" />
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
