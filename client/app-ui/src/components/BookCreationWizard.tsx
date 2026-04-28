import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { BOOK_TYPES, BOOK_TYPE_MAP } from '../bookTypes'
import type { Book, FormatSettings } from '../types'
import { LayoutSelector, LAYOUT_OPTIONS } from './LayoutSelector'
import { SourceLibraryPane } from './SourceLibraryPane'
import { Button } from './ui/Button'
import { Card } from './ui/Card'
import { TextAreaField, TextField } from './ui/FormField'
import { OptionCard } from './ui/OptionCard'
import { Stepper } from './ui/Stepper'

const STEPS = ['Type', 'Mode', 'Details', 'Format', 'Sources']

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
  const [formatSettings, setFormatSettings] = useState<FormatSettings>(LAYOUT_OPTIONS[0])
  const [book, setBook] = useState<Book | null>(null)
  const [sources, setSources] = useState<any[]>([])
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)

  const selectedType = useMemo(() => BOOK_TYPE_MAP[bookTypeId], [bookTypeId])
  const stepIndex = step === 'book-type' ? 0 : step === 'creation-mode' ? 1 : step === 'book-details' ? 2 : step === 'format-selection' ? 3 : 4

  useEffect(() => {
    setCreationMode(selectedType.recommendedMode)
    const matching = LAYOUT_OPTIONS.find((l) => l.selected_layout_id === selectedType.defaultFormat)
    if (matching) setFormatSettings(matching)
  }, [bookTypeId])

  async function createBookBase() {
    setIsSubmitting(true)
    const commonPayload = {
      title: title || 'Untitled', topic, objective, target_audience: audience, tone: tone || selectedType.defaultTone,
      genre: selectedType.displayName, book_type_id: bookTypeId, creation_mode: creationMode,
      layout_template: formatSettings.selected_layout_id, format_settings: formatSettings,
    }
    try {
      if (creationMode === 'expert') {
        const project = await api.createProject({ name: title || selectedType.displayName, description: topic, content_direction: selectedType.displayName, audience, objective, status: 'draft' })
        const created = await api.createProjectBook(project.id, commonPayload)
        setBook(created)
        setSources(await api.listSources(project.id))
        setStep('expert-source-setup')
        return
      }
      onCreated(await api.createBook(commonPayload))
    } finally {
      setIsSubmitting(false)
    }
  }

  const placeholders = bookTypeId.includes('fiction')
    ? { topic: 'Where does the story begin, who matters, and what tension pulls the reader in?', audience: 'Reader / audience (optional)', objective: 'What feeling or arc should the book carry?' }
    : bookTypeId.includes('finance')
      ? { topic: 'What finance concept, operating problem, or decision context should this explain?', audience: 'CFOs, finance teams, founders, investors…', objective: 'What decision or understanding should this support?' }
      : { topic: 'What campaign, category, product, or market problem should this book shape?', audience: 'Who is this for? CMOs, founders, buyers, customers…', objective: 'What should the reader understand, believe, or do after reading?' }

  return (
    <div className="wizard-shell flow-background">
      <div className="gradient-orb gradient-orb--one" />
      <div className="gradient-orb gradient-orb--two" />
      <Card className="wizard-card glass-card">
        <header className="wizard-header">
          <div>
            <p className="kicker">Immersive setup</p>
            <h2>{step === 'book-type' ? 'What are you designing?' : step === 'creation-mode' ? 'How do you want to build it?' : step === 'book-details' ? 'Have you thought of a title?' : step === 'format-selection' ? 'Pick your format style' : 'Add your source material'}</h2>
          </div>
          <Stepper steps={creationMode === 'expert' ? STEPS : STEPS.slice(0, 4)} current={stepIndex} />
        </header>

        {step === 'book-type' ? (
          <div className="wizard-grid">
            {BOOK_TYPES.map((t) => (
              <OptionCard
                key={t.id}
                title={t.shortLabel}
                subtitle={t.displayName}
                selected={bookTypeId === t.id}
                onClick={() => setBookTypeId(t.id)}
                meta={<><span className="chip">{`Recommended: ${t.recommendedMode}`}</span><span className="chip muted">{t.sourcePolicy}</span></>}
              >
                <p>{t.description}</p>
              </OptionCard>
            ))}
          </div>
        ) : null}

        {step === 'creation-mode' ? (
          <div className="wizard-mode-grid">
            <OptionCard title="Classical" subtitle="Build page by page" selected={creationMode === 'classical'} disabled={Boolean(selectedType.hardDisabledModes?.includes('classical') || !selectedType.allowedModes.includes('classical'))} onClick={() => setCreationMode('classical')} meta={selectedType.recommendedMode === 'classical' ? <span className="chip">Recommended</span> : null}>
              <ul><li>Write one page at a time</li><li>Generate, edit, approve</li><li>Best for fiction, memoir, illustrated books</li></ul>
            </OptionCard>
            <OptionCard title="Expert" subtitle="Upload first, generate draft" selected={creationMode === 'expert'} disabled={Boolean(selectedType.hardDisabledModes?.includes('expert') || !selectedType.allowedModes.includes('expert'))} onClick={() => setCreationMode('expert')} meta={selectedType.recommendedMode === 'expert' ? <span className="chip">Recommended</span> : null}>
              <ul><li>Upload docs, notes, images</li><li>Generate multi-page draft</li><li>Edit page by page</li></ul>
            </OptionCard>
          </div>
        ) : null}

        {step === 'book-details' ? (
          <div className="wizard-details-grid">
            <div>
              <TextField label="Title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="The Future of Work" />
              <TextAreaField label="What is the book about?" value={topic} onChange={(e) => setTopic(e.target.value)} placeholder={placeholders.topic} rows={4} />
              <TextField label="Audience" value={audience} onChange={(e) => setAudience(e.target.value)} placeholder={placeholders.audience} />
              <TextAreaField label="Objective" value={objective} onChange={(e) => setObjective(e.target.value)} placeholder={placeholders.objective} rows={3} />
            </div>
            <Card className="helper-card editor-panel"><h4>{selectedType.displayName}</h4><p>{selectedType.description}</p><p>Mode: <strong>{creationMode}</strong></p><p>Tone: {selectedType.defaultTone}</p></Card>
          </div>
        ) : null}

        {step === 'format-selection' ? <div><LayoutSelector selected={formatSettings} onSelect={setFormatSettings} /></div> : null}

        {step === 'expert-source-setup' ? (
          <div>
            <p className="muted">Upload files, add notes, select relevant assets, then generate a draft. You can also skip and start from the workspace.</p>
            {book?.project_id ? <SourceLibraryPane projectId={book.project_id} sources={sources} onRefresh={async () => setSources(await api.listSources(book.project_id!))} selected={selectedSourceIds} setSelected={setSelectedSourceIds} /> : null}
          </div>
        ) : null}

        <footer className="wizard-footer">
          <Button variant="ghost" onClick={onCancel} disabled={isSubmitting}>Cancel</Button>
          {step !== 'book-type' ? <Button variant="secondary" onClick={() => setStep(step === 'creation-mode' ? 'book-type' : step === 'book-details' ? 'creation-mode' : step === 'format-selection' ? 'book-details' : 'format-selection')} disabled={isSubmitting}>Back</Button> : null}
          {step === 'book-type' ? <Button variant="primary" onClick={() => setStep('creation-mode')} disabled={isSubmitting}>Continue</Button> : null}
          {step === 'creation-mode' ? <Button variant="primary" onClick={() => setStep('book-details')} disabled={isSubmitting}>Continue</Button> : null}
          {step === 'book-details' ? <Button variant="primary" onClick={() => setStep('format-selection')} disabled={isSubmitting}>Continue</Button> : null}
          {step === 'format-selection' ? <Button variant="primary" onClick={() => void createBookBase()} disabled={isSubmitting}>{isSubmitting ? 'Creating…' : 'Create book'}</Button> : null}
          {step === 'expert-source-setup' ? (
            <>
              <Button variant="secondary" onClick={() => { if (book) onCreated(book) }} disabled={isSubmitting}>Skip and open workspace</Button>
              <Button variant="primary" onClick={async () => {
                if (!book) return
                setIsSubmitting(true)
                try {
                  await api.generateDraft(book.id, { target_page_count: 8, source_asset_ids: selectedSourceIds, book_type_id: book.book_type_id, creation_mode: 'expert' })
                  onCreated(await api.getBook(book.id))
                } finally {
                  setIsSubmitting(false)
                }
              }} disabled={isSubmitting}>{isSubmitting ? 'Generating…' : 'Generate draft'}</Button>
            </>
          ) : null}
        </footer>
      </Card>
    </div>
  )
}
