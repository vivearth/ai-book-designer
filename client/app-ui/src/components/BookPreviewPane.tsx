import type { Book, Page } from '../types'
import { BookCover } from './BookCover'
import { PagePreview } from './PagePreview'
import { PageNavigator } from './PageNavigator'

type ActiveTarget = { kind: 'cover' } | { kind: 'page'; pageId: string } | { kind: 'new-page' }

export function BookPreviewPane({ book, pages, activeTarget, layoutOverride, onSelectCover, onSelectPage, onCreateNextPage, onTextSave, onImageSelect }: {
  book: Book
  pages: Page[]
  activeTarget: ActiveTarget
  layoutOverride?: Record<string, unknown> | null
  onSelectCover: () => void
  onSelectPage: (pageId: string) => void
  onCreateNextPage: () => void
  onTextSave?: (page: Page, nextText: string) => Promise<void> | void
  onImageSelect?: (imageId: string) => void
}) {
  const activePage = activeTarget.kind === 'page' ? pages.find((page) => page.id === activeTarget.pageId) ?? null : null

  return (
    <section className="preview-pane preview-stage glass-card">
      <div className="preview-pane__header"><div><p className="kicker">Live preview stage</p><h2>{book.title}</h2></div>
        <PageNavigator pages={pages} activeTarget={activeTarget} onSelectCover={onSelectCover} onSelectPage={onSelectPage} onCreateNext={onCreateNextPage} />
      </div>
      <div className="preview-workspace"><div className="book-stage"><div className="book-stage__shadow" /><div className="book-sheet">
        {activeTarget.kind === 'cover' ? <BookCover book={book} /> : <PagePreview book={book} page={activePage} layoutOverride={layoutOverride} editable onTextSave={(nextText) => activePage ? onTextSave?.(activePage, nextText) : undefined} onImageSelect={onImageSelect} />}
      </div></div></div>
    </section>
  )
}
