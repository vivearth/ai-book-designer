import { useMemo, useState } from 'react'
import { api } from '../api'
import type { Book, GenerationResponse, Page } from '../types'
import { BookPreviewPane } from './BookPreviewPane'
import { ChatPane } from './ChatPane'
import { DeveloperDiagnostics } from './DeveloperDiagnostics'

type Draft = {
  user_prompt: string
  user_text: string
  instruction: string
  imageFile: File | null
}

const INITIAL_DRAFT: Draft = {
  user_prompt: '',
  user_text: '',
  instruction: 'Shape this into a polished page while preserving the chosen book format and continuity.',
  imageFile: null,
}

export function BookWorkspace({
  book,
  pages,
  setPages,
  refreshBook,
  refreshPages,
  onBack,
  onSelectProject,
  books,
}: {
  book: Book
  pages: Page[]
  setPages: (pages: Page[]) => void
  refreshBook: () => Promise<void>
  refreshPages: () => Promise<void>
  onBack: () => void
  onSelectProject: (book: Book) => void
  books: Book[]
}) {
  const [draft, setDraft] = useState<Draft>(INITIAL_DRAFT)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activePageId, setActivePageId] = useState<string | null>(null)
  const [contextPacket, setContextPacket] = useState<Record<string, unknown> | null>(null)
  const [continuityNotes, setContinuityNotes] = useState<string[]>([])

  const currentPage = useMemo(() => pages.find((page) => page.id === activePageId) ?? pages[pages.length - 1] ?? null, [activePageId, pages])
  const nextPageNumber = (pages[pages.length - 1]?.page_number || 0) + 1

  async function guarded(action: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  async function ensurePage() {
    if (currentPage && currentPage.status !== 'approved') return currentPage
    const page = await api.createPage(book.id, { page_number: nextPageNumber, user_prompt: draft.user_prompt, user_text: draft.user_text })
    await refreshPages()
    setActivePageId(page.id)
    return page
  }

  async function saveDraft() {
    await guarded(async () => {
      const page = currentPage ?? (await ensurePage())
      const updated = await api.updatePage(page.id, { user_prompt: draft.user_prompt, user_text: draft.user_text })
      if (draft.imageFile) {
        await api.uploadImage(page.id, draft.imageFile, 'Page inspiration')
      }
      await refreshPages()
      setActivePageId(updated.id)
    })
  }

  async function generatePage() {
    await guarded(async () => {
      const page = currentPage ?? (await ensurePage())
      await api.updatePage(page.id, { user_prompt: draft.user_prompt, user_text: draft.user_text })
      if (draft.imageFile) {
        await api.uploadImage(page.id, draft.imageFile, 'Page inspiration')
      }
      const result: GenerationResponse = await api.generatePage(page.id, {
        instruction: draft.instruction,
        target_words: 320,
        allow_new_characters: false,
      })
      setContextPacket(result.context_packet)
      setContinuityNotes(result.continuity_notes)
      await refreshPages()
      setActivePageId(result.page.id)
    })
  }

  async function approvePage() {
    if (!currentPage) return
    await guarded(async () => {
      const result = await api.approvePage(currentPage.id)
      await refreshPages()
      setActivePageId(result.id)
    })
  }

  function goToNextPage() {
    setActivePageId(null)
    setDraft(INITIAL_DRAFT)
  }

  return (
    <div className="workspace-shell">
      <header className="workspace-topbar">
        <button type="button" className="ghost-button" onClick={onBack}>Back</button>
        <div>
          <p className="kicker">Editorial workspace</p>
          <h1>{book.title}</h1>
        </div>
        <div className="workspace-projects">
          {books.slice(0, 4).map((item) => (
            <button key={item.id} type="button" className={`project-dot ${item.id === book.id ? 'is-active' : ''}`} onClick={() => onSelectProject(item)}>
              {item.title.slice(0, 1)}
            </button>
          ))}
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="workspace-grid">
        <ChatPane
          pageNumber={currentPage?.page_number || nextPageNumber}
          draft={draft}
          setDraft={setDraft}
          busy={busy}
          currentPage={currentPage}
          onSaveDraft={saveDraft}
          onGenerate={generatePage}
          onApprove={approvePage}
          onNextPage={goToNextPage}
        />
        <BookPreviewPane book={book} pages={pages} activePageId={activePageId} onSelectPage={setActivePageId} />
      </div>

      <DeveloperDiagnostics contextPacket={contextPacket} continuityNotes={continuityNotes} />
    </div>
  )
}
