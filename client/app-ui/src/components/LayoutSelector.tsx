import type { FormatSettings } from '../types'

function LayoutMiniature({ layoutId }: { layoutId: FormatSettings['selected_layout_id'] }) {
  if (layoutId === 'illustrated-story') {
    return (
      <div className="layout-miniature layout-miniature--illustrated-story">
        <div className="layout-miniature__artboard">
          <div className="art-scene art-scene--sun" />
          <div className="art-scene art-scene--hill art-scene--hill-back" />
          <div className="art-scene art-scene--hill art-scene--hill-front" />
          <div className="art-scene art-scene--tree" />
          <div className="art-scene art-scene--character" />
        </div>
        <div className="layout-miniature__caption-lines">
          <span />
          <span />
        </div>
      </div>
    )
  }

  if (layoutId === 'modern-editorial') {
    return (
      <div className="layout-miniature layout-miniature--modern-editorial">
        <div className="layout-miniature__header-strip" />
        <div className="layout-miniature__editorial-grid">
          <div className="layout-miniature__column-lines">
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="layout-miniature__side-card">
            <div className="layout-miniature__quote-chip" />
            <div className="layout-miniature__chart-bars">
              <span />
              <span />
              <span />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="layout-miniature layout-miniature--classic-novel">
      <div className="layout-miniature__chapter-kicker" />
      <div className="layout-miniature__chapter-title" />
      <div className="layout-miniature__ornament" />
      <div className="layout-miniature__prose-lines">
        {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
      </div>
      <div className="layout-miniature__page-number" />
    </div>
  )
}

const LAYOUTS: FormatSettings[] = [
  {
    selected_layout_id: 'classic-novel',
    layout_name: 'Classic Novel',
    page_size: 'A5',
    margin_style: 'wide',
    typography_style: 'classic-serif',
    image_policy: 'minimal',
    preview_scenarios: [
      { id: 'image-only', title: 'Image-only page', description: 'Reserved for atmospheric separators and section openers.' },
      { id: 'text-with-image', title: 'Text with image', description: 'A restrained illustration paired with text.' },
      { id: 'text-only', title: 'Text-only page', description: 'Pure reading rhythm with elegant margins.' },
    ],
  },
  {
    selected_layout_id: 'illustrated-story',
    layout_name: 'Illustrated Story',
    page_size: 'Square',
    margin_style: 'immersive',
    typography_style: 'story-serif',
    image_policy: 'image-led',
    preview_scenarios: [
      { id: 'image-only', title: 'Image-only page', description: 'Full-bleed scenes that carry emotion on their own.' },
      { id: 'text-with-image', title: 'Text with image', description: 'Narration anchored by bold illustration.' },
      { id: 'text-only', title: 'Text-only page', description: 'Quiet breathing room between visual moments.' },
    ],
  },
  {
    selected_layout_id: 'modern-editorial',
    layout_name: 'Modern Editorial',
    page_size: 'A4',
    margin_style: 'balanced',
    typography_style: 'editorial-mix',
    image_policy: 'flexible',
    preview_scenarios: [
      { id: 'image-only', title: 'Image-only page', description: 'Poster-like visual chapters and impact spreads.' },
      { id: 'text-with-image', title: 'Text with image', description: 'Pull-quote and image compositions.' },
      { id: 'text-only', title: 'Text-only page', description: 'Magazine-inspired reading with structured rhythm.' },
    ],
  },
]

export function LayoutSelector({ selected, onSelect }: { selected: FormatSettings; onSelect: (value: FormatSettings) => void }) {
  return (
    <div className="layout-selector">
      {LAYOUTS.map((layout) => {
        const active = layout.selected_layout_id === selected.selected_layout_id
        return (
          <button
            key={layout.selected_layout_id}
            type="button"
            className={`layout-card layout-option-card layout-card--${layout.selected_layout_id} ${active ? 'is-active' : ''}`}
            onClick={() => onSelect(layout)}
          >
            <div className="layout-card__shine" />
            <div className="layout-card__mini-preview">
              <LayoutMiniature layoutId={layout.selected_layout_id} />
            </div>
            <div>
              <strong>{layout.layout_name}</strong>
              <p>{layout.image_policy === 'minimal' ? 'Text-first, elegant serif pages.' : layout.image_policy === 'image-led' ? 'Image-led pages for visual storytelling.' : 'A hybrid magazine-book composition.'}</p>
            </div>
          </button>
        )
      })}
    </div>
  )
}

export const LAYOUT_OPTIONS = LAYOUTS
