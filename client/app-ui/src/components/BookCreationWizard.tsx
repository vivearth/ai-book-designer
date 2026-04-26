import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { BOOK_TYPES, BOOK_TYPE_MAP } from '../bookTypes'
import type { Book, FormatSettings } from '../types'
import { LayoutSelector, LAYOUT_OPTIONS } from './LayoutSelector'
import { SourceLibraryPane } from './SourceLibraryPane'

const DEFAULT_FORMAT = LAYOUT_OPTIONS[0]

type Step = 'book-type' | 'creation-mode' | 'book-details' | 'format-selection' | 'expert-source-setup'

export function BookCreationWizard({ onCreated, onCancel }: { onCreated: (book: Book) => void; onCancel: () => void }) {
  const [step, setStep] = useState<Step>('book-type')
  const [bookTypeId, setBookTypeId] = useState('fiction_novel')
  const [creationMode, setCreationMode] = useState<'classical' | 'expert'>('classical')
  const [title, setTitle] = useState('')
  const [topic, setTopic] = useState('')
  const [objective, setObjective] = useState('')
  const [audience, setAudience] = useState('')
  const [tone, setTone] = useState('')
  const [formatSettings, setFormatSettings] = useState<FormatSettings>(DEFAULT_FORMAT)
  const [book, setBook] = useState<Book | null>(null)
  const [sources, setSources] = useState<any[]>([])
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([])

  const selectedType = useMemo(() => BOOK_TYPE_MAP[bookTypeId], [bookTypeId])

  useEffect(() => {
    setCreationMode(selectedType.defaultMode)
    const matching = LAYOUT_OPTIONS.find((l) => l.selected_layout_id === selectedType.defaultFormat)
    if (matching) setFormatSettings(matching)
  }, [bookTypeId])

  async function createBookBase() {
    const commonPayload = {
      title: title || 'Untitled',
      topic,
      objective,
      target_audience: audience,
      tone: tone || selectedType.defaultTone,
      genre: selectedType.displayName,
      book_type_id: bookTypeId,
      creation_mode: creationMode,
      layout_template: formatSettings.selected_layout_id,
      format_settings: formatSettings,
    }

    if (creationMode === 'expert') {
      const project = await api.createProject({
        name: title || selectedType.displayName,
        description: topic,
        content_direction: selectedType.displayName,
        audience,
        objective,
        status: 'draft',
      })
      const created = await api.createProjectBook(project.id, commonPayload)
      setBook(created)
      setSources(await api.listSources(project.id))
      setStep('expert-source-setup')
      return
    }

    const created = await api.createBook(commonPayload)
    onCreated(created)
  }

  if (step === 'book-type') return <section className="panel"><h2>What type of book are you designing?</h2>{BOOK_TYPES.map((t) => <button key={t.id} onClick={() => setBookTypeId(t.id)}>{t.displayName} · {t.description} · Recommended: {t.defaultMode}</button>)}<button onClick={() => setStep('creation-mode')}>Next</button><button onClick={onCancel}>Cancel</button></section>
  if (step === 'creation-mode') return <section className="panel"><h2>How do you want to build it?</h2>{(['classical', 'expert'] as const).map((m) => <button key={m} disabled={!selectedType.allowedModes.includes(m)} onClick={() => setCreationMode(m)}>{m}</button>)}<button onClick={() => setStep('book-details')}>Next</button></section>
  if (step === 'book-details') return <section className="panel"><h2>Book details</h2><input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" /><textarea value={topic} onChange={(e) => setTopic(e.target.value)} placeholder={bookTypeId.includes('fiction') ? 'Story, characters, setting...' : 'Business problem and perspective...'} /><input value={audience} onChange={(e) => setAudience(e.target.value)} placeholder="Audience" /><textarea value={objective} onChange={(e) => setObjective(e.target.value)} placeholder="Objective" /><button onClick={() => setStep('format-selection')}>Next</button></section>
  if (step === 'format-selection') return <section className="panel"><h2>Format selection</h2><LayoutSelector selected={formatSettings} onSelect={setFormatSettings} /><button onClick={() => void createBookBase()}>Create book</button></section>

  return (
    <section className="panel">
      <h2>Expert source setup</h2>
      {book?.project_id ? <SourceLibraryPane projectId={book.project_id} sources={sources} onRefresh={async () => setSources(await api.listSources(book.project_id!))} selected={selectedSourceIds} setSelected={setSelectedSourceIds} /> : null}
      <div className="row-gap">
        <button onClick={async () => {
          if (!book) return
          await api.generateDraft(book.id, { target_page_count: 8, source_asset_ids: selectedSourceIds, book_type_id: book.book_type_id, creation_mode: 'expert' })
          onCreated(await api.getBook(book.id))
        }}>Generate book draft</button>
        <button onClick={() => { if (book) onCreated(book) }}>Skip and start empty</button>
      </div>
    </section>
  )
}
