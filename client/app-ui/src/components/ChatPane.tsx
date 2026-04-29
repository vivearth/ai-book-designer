import type { Page } from '../types'

type Draft = {
  user_prompt: string
  user_text: string
  instruction: string
  imageFile: File | null
}

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
  onAddImageClick?: () => void
}) {
  return (
    <section className="chat-pane editor-panel glass-card">
      <div className="chat-message chat-message--assistant">
        <p className="chat-message__eyebrow">Page editor</p>
        <h3>Page {pageNumber} · {currentPage?.status || 'draft'}</h3>
      </div>

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
        <div className="chat-actions chat-actions--primary">
          <button type="button" className="premium-button" onClick={onGenerate} disabled={busy}>Generate page</button>
          <button type="button" className="ghost-button" onClick={onAddImageClick}>Add image</button>
        </div>
        <div className="chat-actions chat-actions--secondary">
          <button type="button" className="ghost-button" onClick={onSaveDraft} disabled={busy}>Save draft</button>
          <button type="button" className="secondary-button" onClick={onApprove} disabled={busy || !currentPage}>Approve</button>
          <button type="button" className="ghost-button" onClick={onNextPage} disabled={busy}>Add next page</button>
        </div>
      </article>

      <article className="chat-message chat-message--user">
        <h4>Layout actions</h4>
        <p className="muted">Create Option A and Option B, compare mini previews, then apply one.</p>
        <div className="chat-actions">
          <button type="button" className="premium-button" onClick={onGenerateLayoutOptions} disabled={busy}>Generate 2 Layouts</button>
          {hasExistingLayoutOptions ? <button type="button" className="ghost-button" onClick={onViewLayoutOptions} disabled={busy}>View options</button> : null}
        </div>
      </article>
    </section>
  )
}
