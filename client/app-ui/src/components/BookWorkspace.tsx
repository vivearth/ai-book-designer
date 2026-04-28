import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { BOOK_TYPE_MAP } from '../bookTypes'
import type { Book, GenerationResponse, Page, Project, SourceAsset } from '../types'
import { BookPreviewPane } from './BookPreviewPane'
import { ChatPane } from './ChatPane'
import { DeveloperDiagnostics } from './DeveloperDiagnostics'
import { QualityReportPanel } from './QualityReportPanel'
import { SourceLibraryPane } from './SourceLibraryPane'
import { estimatePageCapacity } from '../utils/pageCapacity'

type Draft = { user_prompt: string; user_text: string; instruction: string; imageFile: File | null }
const INITIAL_DRAFT: Draft = { user_prompt: '', user_text: '', instruction: 'Shape this into a polished page while preserving continuity.', imageFile: null }

export function BookWorkspace({ book, pages, setPages, refreshPages, onBack, onSelectProject, books, project }: {
  book: Book
  pages: Page[]
  setPages: (pages: Page[]) => void
  refreshPages: () => Promise<void>
  onBack: () => void
  onSelectProject: (book: Book) => void
  books: Book[]
  project?: Project | null
}) {
  const [draft, setDraft] = useState<Draft>(INITIAL_DRAFT)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTarget, setActiveTarget] = useState<{ kind: 'cover' } | { kind: 'page'; pageId: string } | { kind: 'new-page' }>({ kind: 'new-page' })
  const [contextPacket, setContextPacket] = useState<Record<string, unknown> | null>(null)
  const [continuityNotes, setContinuityNotes] = useState<string[]>([])
  const [qualityReport, setQualityReport] = useState<any>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [overflowNotice, setOverflowNotice] = useState<string | null>(null)
  const [sources, setSources] = useState<SourceAsset[]>([])
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([])
  const [exportOpen, setExportOpen] = useState(false)
  const [exportBusy, setExportBusy] = useState(false)
  const [includeDraft, setIncludeDraft] = useState(true)
  const [exportError, setExportError] = useState<string | null>(null)
  const [sourcesOpen, setSourcesOpen] = useState(false)

  const sortedPages = useMemo(() => [...pages].sort((a, b) => a.page_number - b.page_number), [pages])
  const currentPage = activeTarget.kind === 'page' ? sortedPages.find((page) => page.id === activeTarget.pageId) ?? null : null
  const nextPageNumber = (sortedPages[sortedPages.length - 1]?.page_number || 0) + 1
  const bookType = BOOK_TYPE_MAP[book.book_type_id] || BOOK_TYPE_MAP.custom
  const expertMode = book.creation_mode === 'expert'

  useEffect(() => {
    if (!sortedPages.length) {
      setActiveTarget({ kind: 'new-page' })
    } else if (activeTarget.kind === 'new-page') {
      setActiveTarget({ kind: 'page', pageId: sortedPages[sortedPages.length - 1].id })
    }
  }, [book.id, sortedPages.length])

  useEffect(() => { if (expertMode && book.project_id) void refreshSources() }, [book.id, book.project_id, expertMode])

  async function refreshSources() {
    if (!book.project_id) return
    setSources(await api.listSources(book.project_id))
  }

  async function guarded(action: () => Promise<void>) {
    setBusy(true); setError(null)
    try { await action() } catch (err) { setError(err instanceof Error ? err.message : 'Something went wrong') } finally { setBusy(false) }
  }

  async function ensurePage() {
    if (currentPage && currentPage.status !== 'approved') return currentPage
    const page = await api.createNextPage(book.id)
    await refreshPages()
    setActiveTarget({ kind: 'page', pageId: page.id })
    return page
  }

  async function saveDraft() {
    await guarded(async () => {
      const page = currentPage ?? (await ensurePage())
      const updated = await api.updatePage(page.id, { user_prompt: draft.user_prompt, user_text: draft.user_text })
      if (draft.imageFile) await api.uploadImage(page.id, draft.imageFile, 'Page inspiration')
      await refreshPages(); setActiveTarget({ kind: 'page', pageId: updated.id })
    })
  }

  async function generatePage() {
    await guarded(async () => {
      const page = currentPage ?? (await ensurePage())
      await api.updatePage(page.id, { user_prompt: draft.user_prompt, user_text: draft.user_text })
      if (draft.imageFile) await api.uploadImage(page.id, draft.imageFile, 'Page inspiration')

      const contentMode = book.book_type_id
      const allowNewCharacters = contentMode.includes('fiction') && (page.page_number === 1 || !book.memory?.global_summary)
      const page_capacity_hint = estimatePageCapacity(book, page)
      const result: GenerationResponse = await api.generatePage(page.id, {
        instruction: draft.instruction,
        allow_new_characters: allowNewCharacters,
        content_mode: contentMode,
        page_capacity_hint,
        selected_source_asset_ids: expertMode ? selectedSourceIds : [],
        auto_retrieve_sources: true,
      })
      setContextPacket(result.context_packet); setContinuityNotes(result.continuity_notes)
      setQualityReport(result.quality_report); setWarnings(result.warnings || [])
      if (result.overflow_created_page) setOverflowNotice(`The page overflowed, so the remaining text continued on Page ${result.overflow_created_page.page_number}.`)
      else setOverflowNotice(result.overflow_warning || null)
      await refreshPages(); setActiveTarget({ kind: 'page', pageId: result.page.id })
    })
  }

  async function approvePage() {
    if (!currentPage) return
    await guarded(async () => {
      const result = await api.approvePage(currentPage.id)
      await refreshPages(); setActiveTarget({ kind: 'page', pageId: result.id })
    })
  }

  async function createNextPage() {
    await guarded(async () => {
      const page = await api.createNextPage(book.id)
      await refreshPages()
      setActiveTarget({ kind: 'page', pageId: page.id })
      setDraft({ ...INITIAL_DRAFT, instruction: draft.instruction })
    })
  }

  async function exportPdf() {
    setExportBusy(true)
    setExportError(null)
    try {
      const response = await api.exportPdf(book.id, { approved_only: !includeDraft })
      window.open(response.download_url, '_blank', 'noopener,noreferrer')
      setExportOpen(false)
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setExportBusy(false)
    }
  }

  const pageStats = useMemo(() => {
    const approved = sortedPages.filter((p) => p.status === 'approved').length
    const generated = sortedPages.filter((p) => p.status === 'generated').length
    const draftCount = sortedPages.length - approved - generated
    return { approved, generated, draftCount }
  }, [sortedPages])

  return (
    <div className="workspace-shell">
      <header className="workspace-topbar">
        <button type="button" className="ghost-button" onClick={onBack}>Back</button>
        <div>
          <p className="kicker">Book studio · {book.creation_mode}</p>
          <h1>{book.title}</h1>
          <small>{bookType.displayName}</small>
        </div>
        <div className="workspace-topbar-actions">
          {expertMode ? <button type="button" className="ghost-button" onClick={() => setSourcesOpen(true)}>Sources</button> : null}
          <button type="button" onClick={() => setExportOpen(true)}>Finish & Export</button>
          <div className="workspace-projects">
          {books.slice(0, 4).map((item) => <button key={item.id} type="button" className={`project-dot ${item.id === book.id ? 'is-active' : ''}`} onClick={() => onSelectProject(item)}>{item.title.slice(0, 1)}</button>)}
          </div>
        </div>
      </header>
      {error ? <div className="error-banner">{error}</div> : null}
      {busy ? <div className="notice-pill">Generating with local model. This can take 1–3 minutes on smaller GPUs.</div> : null}
      {overflowNotice ? <div className="warning-banner">{overflowNotice}</div> : null}
      {warnings.find((w) => /fallback|timeout|ollama/i.test(w)) ? <div className="warning-banner">{warnings.find((w) => /fallback|timeout|ollama/i.test(w))}</div> : null}

      <div className="workspace-grid">
        <div>
          <ChatPane pageNumber={currentPage?.page_number || nextPageNumber} draft={draft} setDraft={setDraft} busy={busy} currentPage={currentPage} onSaveDraft={saveDraft} onGenerate={generatePage} onApprove={approvePage} onNextPage={() => void createNextPage()} />
          {expertMode ? <QualityReportPanel report={qualityReport || undefined} warnings={warnings} /> : null}
        </div>
        <BookPreviewPane book={book} pages={sortedPages} activeTarget={activeTarget} onSelectCover={() => setActiveTarget({ kind: 'cover' })} onSelectPage={(id) => setActiveTarget({ kind: 'page', pageId: id })} onCreateNextPage={() => void createNextPage()} />
      </div>
      {expertMode && sourcesOpen && book.project_id ? (
        <div className="export-modal-backdrop" role="dialog" aria-modal="true">
          <div className="export-modal">
            <h3>Sources</h3>
            <p className="muted">Upload, process, and select source material without leaving page editing.</p>
            <SourceLibraryPane projectId={book.project_id} sources={sources} onRefresh={refreshSources} selected={selectedSourceIds} setSelected={setSelectedSourceIds} />
            <div className="chat-actions">
              <button type="button" className="ghost-button" onClick={() => setSourcesOpen(false)}>Close</button>
            </div>
          </div>
        </div>
      ) : null}

      <DeveloperDiagnostics contextPacket={contextPacket} continuityNotes={continuityNotes} />
      {exportOpen ? (
        <div className="export-modal-backdrop" role="dialog" aria-modal="true">
          <div className="export-modal">
            <h3>Export PDF</h3>
            <p><strong>{book.title}</strong></p>
            <p>{sortedPages.length} pages · {pageStats.approved} approved · {pageStats.generated} generated · {pageStats.draftCount} draft</p>
            <label className="export-choice">
              <input type="checkbox" checked={includeDraft} onChange={(e) => setIncludeDraft(e.target.checked)} />
              Include draft pages
            </label>
            {exportError ? <p className="error-banner">{exportError}</p> : null}
            <div className="chat-actions">
              <button type="button" className="ghost-button" onClick={() => setExportOpen(false)} disabled={exportBusy}>Cancel</button>
              <button type="button" onClick={() => void exportPdf()} disabled={exportBusy}>{exportBusy ? 'Exporting…' : 'Download PDF'}</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
