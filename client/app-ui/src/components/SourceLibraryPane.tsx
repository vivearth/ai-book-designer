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

  return (
    <section className="panel">
      <h3>Source Library</h3>
      <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste campaign notes, insights, reports..." rows={5} />
      <button onClick={async () => { await api.createTextSource(projectId, { text, title: 'Pasted source', source_type: 'note' }); setText(''); await onRefresh() }}>Add text source</button>
      <div className="list-col">
        {sources.map((source) => (
          <label key={source.id} className="source-card">
            <input
              type="checkbox"
              checked={selected.includes(source.id)}
              onChange={(e) => setSelected(e.target.checked ? [...selected, source.id] : selected.filter((id) => id !== source.id))}
            />
            <div><strong>{source.title}</strong><div>{source.source_type} · {source.status}</div></div>
            <button type="button" onClick={async () => { await api.processSource(source.id); await onRefresh() }}>Process</button>
          </label>
        ))}
      </div>
    </section>
  )
}
