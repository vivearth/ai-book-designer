import type { Book, Page } from '../types'
import { BookCover } from './BookCover'
import { PagePreview } from './PagePreview'
import { PageNavigator } from './PageNavigator'

export function BookPreviewPane({ book, pages, activePageId, showCover, onSelectCover, onSelectPage, onCreateNextPage }: {
  book: Book
  pages: Page[]
  activePageId: string | null
  showCover: boolean
  onSelectCover: () => void
  onSelectPage: (pageId: string) => void
  onCreateNextPage: () => void
}) {
  const activePage = pages.find((page) => page.id === activePageId) ?? null

  return (
    <section className="preview-pane">
      <div className="preview-pane__header">
        <div>
          <p className="kicker">Book preview</p>
          <h2>{book.title}</h2>
        </div>
        <PageNavigator pages={pages} activePageId={activePageId} isCoverActive={showCover} onSelectCover={onSelectCover} onSelectPage={onSelectPage} onCreateNext={onCreateNextPage} />
      </div>
      <div className="book-stage">
        <div className="book-stage__shadow" />
        <div className="book-sheet">
          {showCover || !activePage ? <BookCover book={book} /> : <PagePreview book={book} page={activePage} />}
        </div>
      </div>
    </section>
  )
}
