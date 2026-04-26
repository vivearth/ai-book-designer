import type { ReactNode } from 'react'

export function OptionCard({ title, subtitle, meta, selected, disabled, onClick, children }: { title: string; subtitle?: string; meta?: ReactNode; selected?: boolean; disabled?: boolean; onClick?: () => void; children?: ReactNode }) {
  return (
    <button type="button" disabled={disabled} className={`ui-option-card ${selected ? 'is-selected' : ''} ${disabled ? 'is-disabled' : ''}`.trim()} onClick={onClick}>
      <header>
        <h4>{title}</h4>
        {subtitle ? <p>{subtitle}</p> : null}
        {meta ? <div className="ui-meta-row">{meta}</div> : null}
      </header>
      {children ? <div className="ui-option-body">{children}</div> : null}
    </button>
  )
}
