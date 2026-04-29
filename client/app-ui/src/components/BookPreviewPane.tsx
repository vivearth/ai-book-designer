import type { Book, Page } from '../types'
import { BookCover } from './BookCover'
import { PagePreview } from './PagePreview'
import { PageNavigator } from './PageNavigator'

type ActiveTarget = { kind: 'cover' } | { kind: 'page'; pageId: string } | { kind: 'new-page' }

export function BookPreviewPane({ book, pages, activeTarget, onSelectCover, onSelectPage, onCreateNextPage }: {
  book: Book
  pages: Page[]
  activeTarget: ActiveTarget
  onSelectCover: () => void
  onSelectPage: (pageId: string) => void
  onCreateNextPage: () => void
}) {
  const activePage = activeTarget.kind === 'page' ? pages.find((page) => page.id === activeTarget.pageId) ?? null : null

  return (
    <section className="preview-pane preview-stage glass-card">
      <div className="preview-pane__header">
        <div>
          <p className="kicker">Live preview stage</p>
          <h2>{book.title}</h2>
        </div>
        <PageNavigator pages={pages} activeTarget={activeTarget} onSelectCover={onSelectCover} onSelectPage={onSelectPage} onCreateNext={onCreateNextPage} />
      </div>
      <div className="preview-workspace">
        <aside className="page-thumbnail-strip">
          <button type="button" className={`thumb-card ${activeTarget.kind === 'cover' ? 'is-active' : ''}`} onClick={onSelectCover}>
            <span>C</span>
          </button>
          {pages.map((page) => (
            <button key={page.id} type="button" className={`thumb-card ${activeTarget.kind === 'page' && activeTarget.pageId === page.id ? 'is-active' : ''}`} onClick={() => onSelectPage(page.id)}>
              <span>{page.page_number}</span>
            </button>
          ))}
        </aside>
        <div className="book-stage">
          <div className="book-stage__shadow" />
          <div className="book-sheet">
            {activeTarget.kind === 'cover' ? <BookCover book={book} /> : <PagePreview book={book} page={activePage} />}
          </div>
        </div>
      </div>
    </section>
  )
}
