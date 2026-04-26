import type { Book, Page } from '../types'
import { BookCover } from './BookCover'
import { PagePreview } from './PagePreview'
import { PageNavigator } from './PageNavigator'

export function BookPreviewPane({ book, pages, activePageId, onSelectPage, onCreateNextPage }: { book: Book; pages: Page[]; activePageId: string | null; onSelectPage: (pageId: string | null) => void; onCreateNextPage: () => void }) {
  const activePage = pages.find((page) => page.id === activePageId) ?? pages[0] ?? null

  return (
    <section className="preview-pane">
      <div className="preview-pane__header">
        <div>
          <p className="kicker">Book preview</p>
          <h2>{book.title}</h2>
        </div>
        <PageNavigator pages={pages} activePageId={activePageId} onSelectPage={onSelectPage} onCreateNext={onCreateNextPage} />
      </div>
      <div className="book-stage">
        <div className="book-stage__shadow" />
        <div className="book-sheet">
          {activePage ? <PagePreview book={book} page={activePage} /> : <BookCover book={book} />}
        </div>
      </div>
    </section>
  )
}
