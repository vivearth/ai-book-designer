import type { PreviewScenario } from '../types'

export function FormatPreviewStrip({ scenarios }: { scenarios: PreviewScenario[] }) {
  return (
    <div className="format-preview-strip">
      {scenarios.map((scenario) => (
        <article key={scenario.id} className="scenario-card">
          <div className={`scenario-card__visual scenario-card__visual--${scenario.id}`}>
            <span />
            <span />
            <span />
          </div>
          <h4>{scenario.title}</h4>
          <p>{scenario.description}</p>
        </article>
      ))}
    </div>
  )
}
