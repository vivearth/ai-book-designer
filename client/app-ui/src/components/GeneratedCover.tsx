import type { Book } from '../types'

function hashSeed(input: string) {
  let hash = 0
  for (let i = 0; i < input.length; i += 1) {
    hash = input.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash)
}

export function GeneratedCover({ book }: { book: Book }) {
  const seed = hashSeed(`${book.title}-${book.genre}-${book.layout_template}`)
  const angle = 20 + (seed % 40)
  const accentX = 14 + (seed % 36)
  const accentY = 10 + ((seed >> 4) % 32)

  return (
    <div
      className="generated-cover"
      style={{
        background: `linear-gradient(${angle}deg, rgba(247,240,230,0.98), rgba(234,220,200,0.92), rgba(198,161,91,0.92))`,
      }}
    >
      <div className="generated-cover__grain" />
      <div className="generated-cover__shape generated-cover__shape--one" style={{ left: `${accentX}%`, top: `${accentY}%` }} />
      <div className="generated-cover__shape generated-cover__shape--two" style={{ right: `${accentX / 2}%`, bottom: `${accentY}%` }} />
      <div className="generated-cover__meta">{(book.format_settings?.layout_name || 'Editorial').toUpperCase()}</div>
      <h2>{book.title || 'Untitled'}</h2>
      <p>{book.topic || book.genre || 'A book taking shape, page by page.'}</p>
    </div>
  )
}
