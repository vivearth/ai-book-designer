import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Book, GenerationResponse, Page, Project, SourceAsset } from '../types'
import { BookPreviewPane } from './BookPreviewPane'
import { SourceLibraryPane } from './SourceLibraryPane'
import { QualityReportPanel } from './QualityReportPanel'

export function ProfessionalWorkspace({ project, onBack }: { project: Project; onBack: () => void }) {
  const [books, setBooks] = useState<Book[]>([])
  const [book, setBook] = useState<Book | null>(null)
  const [pages, setPages] = useState<Page[]>([])
  const [sources, setSources] = useState<SourceAsset[]>([])
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [goal, setGoal] = useState('Generate a professional page grounded in selected sources')
  const [skillId, setSkillId] = useState('')
  const [result, setResult] = useState<GenerationResponse | null>(null)
  const [activePageId, setActivePageId] = useState<string | null>(null)

  async function refreshSources() { setSources(await api.listSources(project.id)) }

  useEffect(() => { void (async () => {
    const projectBooks = await api.listProjectBooks(project.id)
    setBooks(projectBooks)
    const active = projectBooks[0] || await api.createProjectBook(project.id, { title: `${project.name} Book Draft` })
    setBook(active)
    const initialPages = await api.listPages(active.id)
    setPages(initialPages)
    setActivePageId(initialPages[0]?.id || null)
    await refreshSources()
  })() }, [project.id])

  async function ensurePage(): Promise<Page> {
    if (!book) throw new Error('No book loaded')
    if (pages.length) return pages[pages.length - 1]
    const created = await api.createPage(book.id, { page_number: 1, user_prompt: goal })
    setPages([created])
    return created
  }

  async function generate() {
    const page = await ensurePage()
    const response = await api.generatePage(page.id, { instruction: goal, skill_id: skillId || undefined, selected_source_asset_ids: selectedSources, auto_retrieve_sources: true })
    setResult(response)
    setPages((prev) => prev.map((p) => p.id === response.page.id ? response.page : p))
  }

  return (
    <div>
      <header className="panel"><button onClick={onBack}>Back</button><h2>{project.name}</h2><p>{project.content_direction} · {project.audience}</p></header>
      <div className="pro-grid">
        <SourceLibraryPane projectId={project.id} sources={sources} onRefresh={refreshSources} selected={selectedSources} setSelected={setSelectedSources} />
        <section className="panel">
          <h3>AI Workbench</h3>
          <textarea rows={6} value={goal} onChange={(e) => setGoal(e.target.value)} />
          <select value={skillId} onChange={(e) => setSkillId(e.target.value)}>
            <option value="">Auto skill</option><option value="marketing_book_page">Marketing book page</option><option value="finance_book_page">Finance explainer page</option>
          </select>
          <button onClick={generate}>Generate professional page</button>
          <div>Selected sources: {selectedSources.length}</div>
        </section>
        <section className="panel">
          {book ? <BookPreviewPane book={book} pages={pages} activePageId={activePageId} onSelectPage={setActivePageId} /> : null}
          <QualityReportPanel report={result?.quality_report} warnings={result?.warnings || []} />
        </section>
      </div>
    </div>
  )
}
