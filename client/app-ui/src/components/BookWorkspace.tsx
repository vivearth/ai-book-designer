import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { BOOK_TYPE_MAP } from '../bookTypes'
import type { Book, GenerationResponse, Page, PageLayoutOption, Project, SourceAsset } from '../types'
import { BookPreviewPane } from './BookPreviewPane'
import { ChatPane } from './ChatPane'
import { DeveloperDiagnostics } from './DeveloperDiagnostics'
import { QualityReportPanel } from './QualityReportPanel'
import { SourceLibraryPane } from './SourceLibraryPane'
import { estimatePageCapacity } from '../utils/pageCapacity'
import { LayoutOptionsPanel } from './LayoutOptionsPanel'

type Draft = { user_prompt: string; user_text: string; instruction: string; imageFile: File | null }
const INITIAL_DRAFT: Draft = { user_prompt: '', user_text: '', instruction: 'Shape this into a polished page while preserving continuity.', imageFile: null }

type RailPanel = 'pages' | 'content' | 'layout' | 'images'

export function BookWorkspace({ book, pages, setPages, refreshPages, onBack, onSelectProject, books }: {
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
  const [uploadedImageSignatureByPageId, setUploadedImageSignatureByPageId] = useState<Record<string, string>>({})
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
  const [layoutOptionsOpen, setLayoutOptionsOpen] = useState(false)
  const [layoutOptions, setLayoutOptions] = useState<PageLayoutOption[]>([])
  const [layoutOptionsBusy, setLayoutOptionsBusy] = useState(false)
  const [hasSavedLayoutOptions, setHasSavedLayoutOptions] = useState(false)
  const [activeRailPanel, setActiveRailPanel] = useState<RailPanel>('content')

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


  useEffect(() => {
    if (activeTarget.kind !== 'page') return
    const exists = sortedPages.some((p) => p.id === activeTarget.pageId)
    if (!exists) setActiveTarget(sortedPages.length ? { kind: 'page', pageId: sortedPages[sortedPages.length - 1].id } : { kind: 'cover' })
  }, [activeTarget, sortedPages])
  useEffect(() => { if (expertMode && book.project_id) void refreshSources() }, [book.id, book.project_id, expertMode])
  useEffect(() => {
    if (!currentPage) {
      setHasSavedLayoutOptions(false)
      return
    }
    void (async () => {
      try {
        const result = await api.listLayoutOptions(currentPage.id)
        setHasSavedLayoutOptions(result.options.length > 0)
      } catch {
        setHasSavedLayoutOptions(Boolean(currentPage.selected_layout_option_id))
      }
    })()
  }, [currentPage?.id])


  function hasValidLayoutSchema(page: Page | null | undefined) {
    return Boolean(page?.layout_json && (page.layout_json as any).layout_schema === 'page-layout-1' && Array.isArray((page.layout_json as any).elements) && (page.layout_json as any).elements.length > 0)
  }

  async function refreshPagesAndGetPage(pageId: string): Promise<Page | null> {
    const latestPages = await api.listPages(book.id)
    setPages(latestPages)
    return latestPages.find((item) => item.id === pageId) || null
  }

  async function refreshSources() {
    if (!book.project_id) return
    setSources(await api.listSources(book.project_id))
  }

  async function guarded(action: () => Promise<void>) {
    setBusy(true); setError(null)
    try { await action() } catch (err) { setError(err instanceof Error ? err.message : 'Something went wrong') } finally { setBusy(false) }
  }

  async function uploadSelectedImageOnce(page: Page) {
    if (!draft.imageFile) return
    const signature = `${draft.imageFile.name}:${draft.imageFile.size}:${draft.imageFile.lastModified}`
    if (uploadedImageSignatureByPageId[page.id] === signature) return
    await api.uploadImage(page.id, draft.imageFile, 'Page inspiration')
    setUploadedImageSignatureByPageId((prev) => ({ ...prev, [page.id]: signature }))
    setDraft((prev) => ({ ...prev, imageFile: null }))
  }

  async function ensurePage() {
    if (currentPage && currentPage.status !== 'approved') return currentPage
    const created = await api.createNextPage(book.id)
    const refreshed = await refreshPagesAndGetPage(created.id)
    const page = refreshed || created
    setActiveTarget({ kind: 'page', pageId: page.id })
    return page
  }

  async function saveDraft() {
    await guarded(async () => {
      const page = currentPage ?? (await ensurePage())
      const updated = await api.updatePage(page.id, { user_prompt: draft.user_prompt, user_text: draft.user_text })
      await uploadSelectedImageOnce(page)
      await refreshPages(); setActiveTarget({ kind: 'page', pageId: updated.id })
    })
  }

  async function generatePage() {
    await guarded(async () => {
      const page = currentPage ?? (await ensurePage())
      await api.updatePage(page.id, { user_prompt: draft.user_prompt, user_text: draft.user_text })
      await uploadSelectedImageOnce(page)

      const allowNewCharacters = book.book_type_id.includes('fiction') && (page.page_number === 1 || !book.memory?.global_summary)
      const page_capacity_hint = estimatePageCapacity(book, page)
      const result: GenerationResponse = await api.generatePage(page.id, {
        instruction: draft.instruction,
        allow_new_characters: allowNewCharacters,
        content_mode: book.book_type_id,
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
      const created = await api.createNextPage(book.id)
      const refreshed = await refreshPagesAndGetPage(created.id)
      const page = hasValidLayoutSchema(created) ? created : (refreshed || created)
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

  async function generateLayoutOptions() {
    setLayoutOptionsBusy(true)
    setError(null)
    try {
      const page = currentPage ?? (await ensurePage())
      const hasDraftInput = Boolean(draft.user_prompt.trim() || draft.user_text.trim() || draft.imageFile)
      const hasSavedContent = Boolean(page.final_text || page.generated_text || page.user_text || page.images.length)
      if (!hasDraftInput && !hasSavedContent) {
        setError('Add page text or an image before generating layout options.')
        return
      }

      const updated = await api.updatePage(page.id, { user_prompt: draft.user_prompt, user_text: draft.user_text })
      await uploadSelectedImageOnce(updated)
      await refreshPages()
      setActiveTarget({ kind: 'page', pageId: updated.id })
      const latestPages = await api.listPages(book.id)
      setPages(latestPages)
      const refreshedPage = latestPages.find((item) => item.id === updated.id) || updated
      const result = await api.generateLayoutOptions(updated.id, {
        preserve_text: true,
        option_count: 2,
        page_capacity_hint: estimatePageCapacity(book, refreshedPage),
        instructions: draft.instruction,
      })
      setLayoutOptions(result.options)
      setHasSavedLayoutOptions(result.options.length > 0)
      setWarnings((prev) => [...prev, ...(result.warnings || [])])
      setLayoutOptionsOpen(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not generate layout options')
    } finally {
      setLayoutOptionsBusy(false)
    }
  }

  async function selectLayoutOption(option: PageLayoutOption) {
    if (!currentPage) return
    await guarded(async () => {
      const updated = await api.selectLayoutOption(currentPage.id, option.id)
      const refreshed = await refreshPagesAndGetPage(currentPage.id)
      const page = refreshed || updated
      setActiveTarget({ kind: 'page', pageId: page.id })
      setHasSavedLayoutOptions(true)
      setLayoutOptionsOpen(false)
    })
  }

  async function viewLayoutOptions() {
    if (!currentPage) return
    setLayoutOptionsBusy(true)
    setError(null)
    try {
      const result = await api.listLayoutOptions(currentPage.id)
      setLayoutOptions(result.options)
      setHasSavedLayoutOptions(result.options.length > 0)
      setLayoutOptionsOpen(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load layout options')
    } finally {
      setLayoutOptionsBusy(false)
    }
  }

  const pageStats = useMemo(() => {
    const approved = sortedPages.filter((p) => p.status === 'approved').length
    const generated = sortedPages.filter((p) => p.status === 'generated').length
    const draftCount = sortedPages.length - approved - generated
    return { approved, generated, draftCount }
  }, [sortedPages])

  return (
    <div className="workspace-shell studio-shell flow-background">
      <header className="workspace-topbar">
        <button type="button" className="ghost-button workspace-back-button" onClick={onBack}>← Back</button>
        <div>
          <p className="kicker">{book.creation_mode} mode · {bookType.displayName}</p>
          <h1>{book.title}</h1>
            <small className="muted">Saved changes sync while you work.</small>
        </div>
        <div className="workspace-topbar-actions">
          {expertMode ? <button type="button" className="ghost-button" onClick={() => setSourcesOpen(true)}>Sources</button> : null}
          <button type="button" className="premium-button" onClick={() => setExportOpen(true)}>Finish & Export</button>
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
        <div className="workspace-editor-shell">
          <section className="glass-card rail-panel page-editor-panel">
            <div className="panel-tabs">
              <button className={activeRailPanel === 'content' ? 'is-active' : ''} onClick={() => setActiveRailPanel('content')}>Content</button>
              <button className={activeRailPanel === 'layout' ? 'is-active' : ''} onClick={() => setActiveRailPanel('layout')}>Layout</button>
              <button className={activeRailPanel === 'images' ? 'is-active' : ''} onClick={() => setActiveRailPanel('images')}>Image</button>
              <button className={activeRailPanel === 'pages' ? 'is-active' : ''} onClick={() => setActiveRailPanel('pages')}>Pages</button>
            </div>
          </section>
          {activeRailPanel === 'pages' ? (
            <section className="glass-card rail-panel">
              <h3>Pages</h3>
              <div className="page-list-panel">
                {sortedPages.map((p) => (
                  <button key={p.id} type="button" className={`page-row ${currentPage?.id === p.id ? 'is-active' : ''}`} onClick={() => setActiveTarget({ kind: 'page', pageId: p.id })}>
                    <span>Page {p.page_number}</span>
                    <small>{p.status}</small>
                  </button>
                ))}
              </div>
              <div className="chat-actions">
                <button type="button" className="ghost-button" onClick={() => void createNextPage()} disabled={busy}>Add next page</button>
              </div>
            </section>
          ) : null}

          {activeRailPanel === 'content' ? (
            <ChatPane
              pageNumber={currentPage?.page_number || nextPageNumber}
              draft={draft}
              setDraft={setDraft}
              busy={busy || layoutOptionsBusy}
              currentPage={currentPage}
              onSaveDraft={saveDraft}
              onGenerate={generatePage}
              onApprove={approvePage}
              onNextPage={() => void createNextPage()}
              onAddImageClick={() => setActiveRailPanel('images')}
            />
          ) : null}

          {activeRailPanel === 'layout' ? (
            <section className="glass-card rail-panel">
              <h3>Layout actions</h3>
              <p className="muted">Generate two visual arrangements for this page without rewriting the text.</p>
              <p className="muted">{currentPage?.selected_layout_option_id ? 'A layout option is currently selected for this page.' : 'No layout option selected yet.'}</p>
              <div className="chat-actions">
                <button type="button" className="premium-button" onClick={() => void generateLayoutOptions()} disabled={busy || layoutOptionsBusy}>Generate 2 Layouts</button>
                {hasSavedLayoutOptions || Boolean(currentPage?.selected_layout_option_id) ? (
                  <button type="button" className="ghost-button" onClick={() => void viewLayoutOptions()} disabled={busy || layoutOptionsBusy}>View options</button>
                ) : null}
              </div>
            </section>
          ) : null}

          {activeRailPanel === 'images' ? (
            <section className="glass-card rail-panel">
              <h3>Image controls</h3>
              <p className="muted">Choose a page image, then save it or generate immediately with it.</p>
              <label className="file-input">
                <span>Upload page image</span>
                <div className="file-input-dropzone">
                  <p>Drop image here or choose file</p>
                  <input type="file" accept="image/*" onChange={(event) => setDraft({ ...draft, imageFile: event.target.files?.[0] ?? null })} />
                </div>
                {draft.imageFile ? <span className="file-chip">{draft.imageFile.name}</span> : <span className="muted">No image selected</span>}
              </label>
              <div className="chat-actions">
                <button type="button" className="ghost-button" onClick={() => setActiveRailPanel('content')}>Back to content</button>
                <button type="button" className="ghost-button" onClick={() => void saveDraft()} disabled={busy}>Save image to page</button>
                <button type="button" className="premium-button" onClick={() => void generatePage()} disabled={busy}>Generate with image</button>
              </div>
            </section>
          ) : null}

          {expertMode ? <QualityReportPanel report={qualityReport || undefined} warnings={warnings} /> : null}
        </div>
        <BookPreviewPane book={book} pages={sortedPages} activeTarget={activeTarget} onSelectCover={() => setActiveTarget({ kind: 'cover' })} onSelectPage={(id) => setActiveTarget({ kind: 'page', pageId: id })} onCreateNextPage={() => void createNextPage()} onImageSelect={() => setActiveRailPanel('images')} onTextSave={async (page, nextText) => {
          const field = page.final_text ? 'final_text' : (page.generated_text ? 'generated_text' : 'user_text')
          await api.updatePage(page.id, { [field]: nextText } as Partial<Page>)
          await refreshPages()
        }} />
      </div>
      {expertMode && sourcesOpen && book.project_id ? (
        <div className="export-modal-backdrop" role="dialog" aria-modal="true">
          <div className="export-modal glass-card">
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
          <div className="export-modal glass-card">
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
              <button type="button" className="premium-button" onClick={() => void exportPdf()} disabled={exportBusy}>{exportBusy ? 'Exporting…' : 'Download PDF'}</button>
            </div>
          </div>
        </div>
      ) : null}
      <LayoutOptionsPanel
        open={layoutOptionsOpen}
        page={currentPage}
        book={book}
        options={layoutOptions}
        selectedOptionId={currentPage?.selected_layout_option_id}
        generating={layoutOptionsBusy}
        onClose={() => setLayoutOptionsOpen(false)}
        onSelect={(option) => void selectLayoutOption(option)}
        onRegenerate={() => void generateLayoutOptions()}
      />
    </div>
  )
}
