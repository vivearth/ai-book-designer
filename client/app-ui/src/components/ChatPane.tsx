import { useEffect, useState } from 'react'
import type { Page } from '../types'

type Draft = {
  user_prompt: string
  user_text: string
  instruction: string
  imageFile: File | null
}

type EditorTab = 'content' | 'layout' | 'design'

export function ChatPane({
  pageNumber,
  draft,
  setDraft,
  busy,
  currentPage,
  onSaveDraft,
  onGenerate,
  onApprove,
  onNextPage,
  onGenerateLayoutOptions,
  onViewLayoutOptions,
  hasExistingLayoutOptions,
  forcedTab,
  onAddImageClick,
}: {
  pageNumber: number
  draft: Draft
  setDraft: (value: Draft) => void
  busy: boolean
  currentPage: Page | null
  onSaveDraft: () => void
  onGenerate: () => void
  onApprove: () => void
  onNextPage: () => void
  onGenerateLayoutOptions: () => void
  onViewLayoutOptions: () => void
  hasExistingLayoutOptions: boolean
  forcedTab?: EditorTab
  onAddImageClick?: () => void
}) {
  const [tab, setTab] = useState<EditorTab>('content')
  useEffect(() => {
    if (forcedTab) setTab(forcedTab)
  }, [forcedTab])

  return (
    <section className="chat-pane editor-panel glass-card">
      <div className="chat-message chat-message--assistant">
        <p className="chat-message__eyebrow">Page editor</p>
        <h3>Page {pageNumber} · {currentPage?.status || 'draft'}</h3>
      </div>

      {!forcedTab ? (
        <div className="panel-tabs">
          <button className={tab === 'content' ? 'is-active' : ''} onClick={() => setTab('content')}>Content</button>
          <button className={tab === 'layout' ? 'is-active' : ''} onClick={() => setTab('layout')}>Layout Options</button>
          <button className={tab === 'design' ? 'is-active' : ''} onClick={() => setTab('design')}>Design</button>
        </div>
      ) : null}

      {tab === 'content' ? (
        <article className="chat-message chat-message--user draft-composer">
          <label>
            Page direction
            <textarea value={draft.user_prompt} onChange={(event) => setDraft({ ...draft, user_prompt: event.target.value })} placeholder="What belongs on this page?" />
          </label>
          <label>
            Rough text / page copy
            <textarea value={draft.user_text} onChange={(event) => setDraft({ ...draft, user_text: event.target.value })} placeholder="Paste rough draft, scene beats, or notes." />
          </label>
          <label>
            Assistant guidance
            <textarea value={draft.instruction} onChange={(event) => setDraft({ ...draft, instruction: event.target.value })} placeholder="Polish prose, preserve continuity, keep tone aligned." />
          </label>
          <p className="muted">Generation can combine your text direction and a reference image.</p>
          <div className="chat-actions">
            <button type="button" className="ghost-button" onClick={() => onAddImageClick?.()}>Add image</button>
            <button type="button" className="ghost-button" onClick={onSaveDraft} disabled={busy}>Save draft</button>
            <button type="button" className="premium-button" onClick={onGenerate} disabled={busy}>Generate page</button>
            <button type="button" className="secondary-button" onClick={onApprove} disabled={busy || !currentPage}>Approve</button>
            <button type="button" className="ghost-button" onClick={onNextPage} disabled={busy}>Add next page</button>
          </div>
        </article>
      ) : null}

      {tab === 'layout' ? (
        <article className="chat-message chat-message--user">
          <h4>Generate layout options</h4>
          <p className="muted">Create Option A and Option B, compare mini previews, then apply one.</p>
          <div className="chat-actions">
            <button type="button" className="premium-button" onClick={onGenerateLayoutOptions} disabled={busy}>Generate 2 Layouts</button>
            {hasExistingLayoutOptions ? <button type="button" className="ghost-button" onClick={onViewLayoutOptions} disabled={busy}>View options</button> : null}
          </div>
        </article>
      ) : null}

      {tab === 'design' ? (
        <article className="chat-message chat-message--user">
          <h4>Design controls</h4>
          <p className="muted">Typography policy and image style controls will live here. Current generation and preview flows remain unchanged.</p>
        </article>
      ) : null}
    </section>
  )
}
