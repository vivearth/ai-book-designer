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
}) {
  return (
    <section className="chat-pane">
      <div className="chat-thread">
        <article className="chat-message chat-message--assistant">
          <p className="chat-message__eyebrow">Book design assistant</p>
          <h3>Tell me what should happen on page {pageNumber}.</h3>
          <p>You can paste rough text, describe the scene, or upload an image. I’ll keep the book format and story memory in mind.</p>
        </article>
        <article className="chat-message chat-message--user draft-composer">
          <label>
            Page direction
            <textarea value={draft.user_prompt} onChange={(event) => setDraft({ ...draft, user_prompt: event.target.value })} placeholder="What belongs on this page?" />
          </label>
          <label>
            Rough text or notes
            <textarea value={draft.user_text} onChange={(event) => setDraft({ ...draft, user_text: event.target.value })} placeholder="Paste a rough draft, scene beats, ideas, or captions." />
          </label>
          <label>
            Assistant instruction
            <textarea value={draft.instruction} onChange={(event) => setDraft({ ...draft, instruction: event.target.value })} placeholder="Polish the prose, keep it calm and literary, maintain continuity." />
          </label>
          <label className="file-input">
            Add a page image
            <input type="file" accept="image/*" onChange={(event) => setDraft({ ...draft, imageFile: event.target.files?.[0] ?? null })} />
            <span>{draft.imageFile?.name || 'No file selected yet'}</span>
          </label>
          <div className="chat-actions">
            <button type="button" className="ghost-button" onClick={onSaveDraft} disabled={busy}>Save draft</button>
            <button type="button" onClick={onGenerate} disabled={busy}>Generate page</button>
            <button type="button" className="secondary-button" onClick={onApprove} disabled={busy || !currentPage}>Approve page</button>
            <button type="button" className="ghost-button" onClick={onNextPage} disabled={busy}>Next page</button>
          </div>
        </article>
        {currentPage ? (
          <article className="chat-message chat-message--assistant generated-note">
            <p className="chat-message__eyebrow">Current page</p>
            <h4>Page {currentPage.page_number} · {currentPage.status}</h4>
            <p>{currentPage.final_text || currentPage.generated_text || currentPage.user_text || 'No page copy yet.'}</p>
          </article>
        ) : null}
      </div>
    </section>
  )
}
