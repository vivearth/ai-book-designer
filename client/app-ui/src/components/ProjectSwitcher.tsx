import type { Book } from '../types'

export function ProjectSwitcher({ books, selectedBookId, onSelect }: { books: Book[]; selectedBookId?: string | null; onSelect: (book: Book) => void }) {
  return (
    <div className="project-switcher">
      {books.map((book) => (
        <button
          key={book.id}
          type="button"
          className={`project-chip ${selectedBookId === book.id ? 'is-active' : ''}`}
          onClick={() => onSelect(book)}
        >
          <span>{book.title}</span>
          <small>{book.genre || 'Book project'}</small>
        </button>
      ))}
    </div>
  )
}
