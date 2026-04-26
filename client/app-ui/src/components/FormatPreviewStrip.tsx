import type { FormatSettings, PreviewScenario } from '../types'

function ScenarioVisual({ layoutId, scenarioId }: { layoutId: FormatSettings['selected_layout_id']; scenarioId: PreviewScenario['id'] }) {
  return (
    <div className={`scenario-card__visual scenario-card__visual--${layoutId} scenario-card__visual--${scenarioId}`}>
      <div className="scenario-visual__canvas">
        <div className="scenario-visual__headline" />
        <div className="scenario-visual__image scene-illustration">
          <div className="scene-illustration__sun" />
          <div className="scene-illustration__hill scene-illustration__hill--back" />
          <div className="scene-illustration__hill scene-illustration__hill--front" />
          <div className="scene-illustration__tree" />
        </div>
        <div className="scenario-visual__columns">
          <span />
          <span />
          <span />
        </div>
        <div className="scenario-visual__quote" />
        <div className="scenario-visual__bars">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  )
}

export function FormatPreviewStrip({ formatSettings }: { formatSettings: FormatSettings }) {
  return (
    <div className="format-preview-strip">
      {formatSettings.preview_scenarios.map((scenario) => (
        <article
          key={scenario.id}
          className={`scenario-card scenario-card--${formatSettings.selected_layout_id} scenario-card--${scenario.id}`}
        >
          <ScenarioVisual layoutId={formatSettings.selected_layout_id} scenarioId={scenario.id} />
          <h4>{scenario.title}</h4>
          <p>{scenario.description}</p>
        </article>
      ))}
    </div>
  )
}
