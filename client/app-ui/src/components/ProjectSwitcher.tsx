import type { Book } from '../types'

export function ProjectSwitcher({ books, selectedBookId, onSelect }: { books: Book[]; selectedBookId?: string | null; onSelect: (book: Book) => void }) {
  return (
    <div className="project-switcher project-switcher--shelf">
      {books.map((book) => (
        <button
          key={book.id}
          type="button"
          className={`project-chip project-chip--book ${selectedBookId === book.id ? 'is-active' : ''}`}
          onClick={() => onSelect(book)}
        >
          <span className="project-chip__spine" />
          <span className="project-chip__meta">
            <strong>{book.title}</strong>
            <small>{book.genre || 'Book project'}</small>
          </span>
          <em>{book.status}</em>
        </button>
      ))}
    </div>
  )
}
