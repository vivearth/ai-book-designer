export function SegmentedControl<T extends string>({ options, value, onChange }: { options: Array<{ value: T; label: string }>; value: T; onChange: (value: T) => void }) {
  return <div className="ui-segmented">{options.map((o) => <button key={o.value} type="button" className={value === o.value ? 'is-active' : ''} onClick={() => onChange(o.value)}>{o.label}</button>)}</div>
}
