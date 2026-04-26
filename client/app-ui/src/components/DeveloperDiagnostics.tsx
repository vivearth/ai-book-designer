export function DeveloperDiagnostics({ contextPacket, continuityNotes }: { contextPacket: Record<string, unknown> | null; continuityNotes: string[] }) {
  return (
    <details className="developer-diagnostics">
      <summary>Developer diagnostics</summary>
      <div className="developer-diagnostics__content">
        <section>
          <h4>Context packet</h4>
          <pre>{contextPacket ? JSON.stringify(contextPacket, null, 2) : 'No context packet yet.'}</pre>
        </section>
        <section>
          <h4>Continuity notes</h4>
          {continuityNotes.length ? <ul>{continuityNotes.map((note) => <li key={note}>{note}</li>)}</ul> : <p>No notes yet.</p>}
        </section>
      </div>
    </details>
  )
}
