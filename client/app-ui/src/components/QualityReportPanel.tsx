export function QualityReportPanel({ report, warnings }: { report?: { score?: number; flags?: Record<string, boolean>; issues?: string[] }; warnings: string[] }) {
  return (
    <section className="panel">
      <h3>Quality & Source Review</h3>
      <div>Score: <strong>{report?.score ?? '—'}</strong></div>
      {report?.issues?.length ? <ul>{report.issues.map((issue) => <li key={issue}>{issue}</li>)}</ul> : <p>No major issues detected.</p>}
      {warnings.length ? <ul>{warnings.map((w) => <li key={w}>{w}</li>)}</ul> : null}
    </section>
  )
}
