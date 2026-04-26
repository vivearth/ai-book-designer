import { useState } from 'react'
import { api } from '../api'
import type { SourceAsset } from '../types'

export function SourceLibraryPane({ projectId, sources, onRefresh, selected, setSelected }: {
  projectId: string
  sources: SourceAsset[]
  onRefresh: () => Promise<void>
  selected: string[]
  setSelected: (ids: string[]) => void
}) {
  const [text, setText] = useState('')

  async function uploadFiles(files: FileList | null) {
    if (!files) return
    for (const file of Array.from(files)) {
      await api.uploadSource(projectId, file, { source_type: 'other' })
    }
    await onRefresh()
  }

  return (
    <section className="panel">
      <h3>Source Library</h3>
      <input type="file" multiple onChange={(e) => void uploadFiles(e.target.files)} />
      <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste campaign notes, insights, reports..." rows={5} />
      <div className="row-gap">
        <button onClick={async () => { if (!text.trim()) return; await api.createTextSource(projectId, { text, title: 'Pasted source', source_type: 'note' }); setText(''); await onRefresh() }}>Add text source</button>
        <button onClick={async () => { for (const s of sources.filter((x) => x.status !== 'processed')) await api.processSource(s.id); await onRefresh() }}>Process all</button>
        <button onClick={() => setSelected(sources.map((s) => s.id))}>Select all</button>
      </div>
      <div className="list-col">
        {sources.map((source) => (
          <label key={source.id} className="source-card">
            <input type="checkbox" checked={selected.includes(source.id)} onChange={(e) => setSelected(e.target.checked ? [...selected, source.id] : selected.filter((id) => id !== source.id))} />
            <div>
              <strong>{source.title}</strong>
              <div>{source.source_type} · {source.status}</div>
              {source.summary ? <small>{source.summary.slice(0, 110)}...</small> : null}
            </div>
            <button type="button" onClick={async () => { await api.processSource(source.id); await onRefresh() }}>Process</button>
          </label>
        ))}
      </div>
    </section>
  )
}
