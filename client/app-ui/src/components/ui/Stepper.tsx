export function Stepper({ steps, current }: { steps: string[]; current: number }) {
  return (
    <div className="ui-stepper">
      {steps.map((step, idx) => (
        <div key={step} className={`ui-step ${idx === current ? 'is-current' : idx < current ? 'is-done' : ''}`}>
          <span className="ui-step-dot">{idx + 1}</span>
          <span>{step}</span>
        </div>
      ))}
    </div>
  )
}
