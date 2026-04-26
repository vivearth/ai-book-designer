import { useState } from 'react'
import { api } from '../api'
import type { SourceAsset } from '../types'
import { Button } from './ui/Button'
import { Card } from './ui/Card'
import { TextAreaField, TextField } from './ui/FormField'

export function SourceLibraryPane({ projectId, sources, onRefresh, selected, setSelected }: {
  projectId: string
  sources: SourceAsset[]
  onRefresh: () => Promise<void>
  selected: string[]
  setSelected: (ids: string[]) => void
}) {
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')

  async function uploadFiles(files: FileList | null) {
    if (!files) return
    for (const file of Array.from(files)) await api.uploadSource(projectId, file, { source_type: 'other' })
    await onRefresh()
  }

  return (
    <div className="source-setup-shell">
      <Card className="upload-dropzone">
        <label>
          <strong>Upload source files</strong>
          <p>Drop PDFs, markdown, text, images, and notes.</p>
          <div className="file-input-dropzone">
            <p>Drop files here or choose files</p>
            <input type="file" multiple onChange={(e) => void uploadFiles(e.target.files)} />
          </div>
        </label>
      </Card>

      <Card>
        <TextField label="Source title (optional)" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Campaign notes / advisory memo" />
        <TextAreaField label="Paste source text" value={text} onChange={(e) => setText(e.target.value)} rows={4} placeholder="Paste long notes or draft material here…" />
        <div className="row-gap">
          <Button onClick={async () => { if (!text.trim()) return; await api.createTextSource(projectId, { text, title: title || 'Pasted source', source_type: 'note' }); setText(''); setTitle(''); await onRefresh() }}>Add source</Button>
          <Button variant="secondary" onClick={async () => { for (const s of sources.filter((x) => x.status !== 'processed')) await api.processSource(s.id); await onRefresh() }}>Process all</Button>
          <Button variant="ghost" onClick={() => setSelected(sources.map((s) => s.id))}>Select all</Button>
        </div>
      </Card>

      <div className="source-list-grid">
        {sources.length === 0 ? <Card><p className="muted">No sources yet. Upload files or paste source text to generate a stronger draft.</p></Card> : null}
        {sources.map((source) => (
          <Card key={source.id} className={`source-item ${selected.includes(source.id) ? 'is-selected' : ''}`}>
            <div className="source-item-head">
              <label><input type="checkbox" checked={selected.includes(source.id)} onChange={(e) => setSelected(e.target.checked ? [...selected, source.id] : selected.filter((id) => id !== source.id))} /> <strong>{source.title}</strong></label>
              <span className="chip muted">{source.status}</span>
            </div>
            <small>{source.source_type}</small>
            {source.summary ? <p>{source.summary.slice(0, 130)}…</p> : <p className="muted">No summary yet.</p>}
            <Button size="sm" variant="secondary" onClick={async () => { await api.processSource(source.id); await onRefresh() }}>Process</Button>
          </Card>
        ))}
      </div>
    </div>
  )
}
