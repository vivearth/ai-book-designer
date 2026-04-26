import { useState } from 'react'
import { api } from '../api'
import type { Book, FormatSettings } from '../types'
import { FormatPreviewStrip } from './FormatPreviewStrip'
import { LayoutSelector, LAYOUT_OPTIONS } from './LayoutSelector'

const STORAGE_KEY = 'book-designer:last-starter-settings'

const DEFAULT_FORMAT = LAYOUT_OPTIONS[0]

export function BookOnboarding({ onCreated }: { onCreated: (book: Book) => void }) {
  const stored = localStorage.getItem(STORAGE_KEY)
  const storedData = stored ? JSON.parse(stored) : {}

  const [title, setTitle] = useState(storedData.title || '')
  const [topic, setTopic] = useState(storedData.topic || '')
  const [genre, setGenre] = useState(storedData.genre || 'Fiction')
  const [customGenre, setCustomGenre] = useState(storedData.customGenre || '')
  const [coverFile, setCoverFile] = useState<File | null>(null)
  const [formatSettings, setFormatSettings] = useState<FormatSettings>(storedData.formatSettings || DEFAULT_FORMAT)
  const [reviewingFormat, setReviewingFormat] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const resolvedGenre = genre === 'Custom' ? customGenre : genre

  async function createBook() {
    setBusy(true)
    setError(null)
    try {
      const payload = {
        title: title.trim() || 'Untitled',
        topic,
        genre: resolvedGenre,
        writing_style: 'Warm, literary, page-aware storytelling',
        tone: 'Warm editorial',
        page_size: formatSettings.page_size,
        layout_template: formatSettings.selected_layout_id,
        format_settings: formatSettings,
      }
      const book = await api.createBook(payload)
      if (coverFile) {
        const updated = await api.uploadCover(book.id, coverFile)
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ title, topic, genre, customGenre, formatSettings }))
        onCreated(updated)
        return
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ title, topic, genre, customGenre, formatSettings }))
      onCreated(book)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create the book')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="onboarding-shell">
      <div className="onboarding-intro">
        <p className="kicker">New book setup</p>
        <h1>Start with the direction, not the bureaucracy.</h1>
        <p>Choose the tone of the object you’re making, then move straight into shaping pages with the assistant.</p>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="onboarding-grid">
        <article className="onboarding-card">
          <h3>Have you thought about the title yet?</h3>
          <p>You can change it later.</p>
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Untitled" />
        </article>

        <article className="onboarding-card onboarding-card--wide">
          <h3>Describe what the book is about.</h3>
          <p>This gives the assistant grounding for every page.</p>
          <textarea value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="What is this book trying to hold together?" />
        </article>

        <article className="onboarding-card">
          <h3>Genre</h3>
          <p>Optional. You can refine this later.</p>
          <div className="genre-options">
            {['Fiction', 'Non-fiction', 'Children\'s book', 'Memoir', 'Poetry', 'Custom'].map((option) => (
              <button key={option} type="button" className={`genre-pill ${genre === option ? 'is-active' : ''}`} onClick={() => setGenre(option)}>
                {option}
              </button>
            ))}
          </div>
          {genre === 'Custom' ? <input value={customGenre} onChange={(event) => setCustomGenre(event.target.value)} placeholder="Custom genre" /> : null}
        </article>

        <article className="onboarding-card">
          <h3>Cover inspiration</h3>
          <p>Have a cover image, moodboard, or visual inspiration? You can add it now and change it later.</p>
          <label className="file-input inline-upload">
            <input type="file" accept="image/*" onChange={(event) => setCoverFile(event.target.files?.[0] ?? null)} />
            <span>{coverFile?.name || 'Upload optional inspiration'}</span>
          </label>
        </article>
      </div>

      <article className="onboarding-card onboarding-card--full">
        <div className="format-header">
          <div>
            <p className="kicker">Book formatting settings</p>
            <h3>Choose the visual language of the book.</h3>
          </div>
          <p>You can change this later, but it’s the direction the assistant will keep in mind from the start.</p>
        </div>

        <LayoutSelector selected={formatSettings} onSelect={(value) => { setFormatSettings(value); setReviewingFormat(true) }} />

        {reviewingFormat ? (
          <div className="format-review">
            <div>
              <h4>{formatSettings.layout_name}</h4>
              <p>See how this format behaves before you commit.</p>
            </div>
            <FormatPreviewStrip scenarios={formatSettings.preview_scenarios} />
            <div className="format-review__actions">
              <button type="button" onClick={createBook} disabled={busy}>Use this format</button>
              <button type="button" className="ghost-button" onClick={() => setReviewingFormat(false)}>Change format</button>
            </div>
          </div>
        ) : null}
      </article>
    </section>
  )
}
