import type { Book, Page } from '../types'
import { BookCover } from './BookCover'
import { PagePreview } from './PagePreview'

export function BookPreviewPane({ book, pages, activePageId, onSelectPage }: { book: Book; pages: Page[]; activePageId: string | null; onSelectPage: (pageId: string | null) => void }) {
  const activePage = pages.find((page) => page.id === activePageId) ?? pages[0] ?? null
  const previewMode = activePage?.images?.length ? 'text-with-image' : 'text-only'

  return (
    <section className="preview-pane">
      <div className="preview-pane__header">
        <div>
          <p className="kicker">Book preview</p>
          <h2>{book.title}</h2>
        </div>
        <nav className="page-nav">
          <button type="button" className={!activePage ? 'is-active' : ''} onClick={() => onSelectPage(null)}>Cover</button>
          {pages.map((page) => (
            <button key={page.id} type="button" className={activePage?.id === page.id ? 'is-active' : ''} onClick={() => onSelectPage(page.id)}>
              Page {page.page_number}
            </button>
          ))}
        </nav>
      </div>
      <div className="book-stage">
        <div className="book-stage__shadow" />
        <div className="book-sheet">
          {activePage ? <PagePreview page={activePage} mode={previewMode} /> : <BookCover book={book} />}
        </div>
      </div>
    </section>
  )
}
