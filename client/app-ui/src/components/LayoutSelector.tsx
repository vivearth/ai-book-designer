import type { FormatSettings } from '../types'

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
            className={`layout-card ${active ? 'is-active' : ''}`}
            onClick={() => onSelect(layout)}
          >
            <div className="layout-card__shine" />
            <div className="layout-card__mini-preview">
              <div className={`mini-page mini-page--${layout.selected_layout_id}`}>
                <span />
                <span />
                <span />
              </div>
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
