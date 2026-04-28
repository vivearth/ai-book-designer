export type BookTypeConfig = {
  id: string
  shortLabel: string
  displayName: string
  description: string
  recommendedMode: 'classical' | 'expert'
  allowedModes: Array<'classical' | 'expert'>
  discouragedModes?: Array<'classical' | 'expert'>
  hardDisabledModes?: Array<'classical' | 'expert'>
  defaultSkill: string
  sourcePolicy: 'optional' | 'recommended' | 'required'
  defaultFormat: 'classic-novel' | 'illustrated-story' | 'modern-editorial'
  defaultTone: string
}

export const BOOK_TYPES: BookTypeConfig[] = [
  { id: 'fiction_novel', shortLabel: 'Novel', displayName: 'Fiction Novel', description: 'Long-form narrative fiction, scenes and characters.', recommendedMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'fiction_book_page', sourcePolicy: 'optional', defaultFormat: 'classic-novel', defaultTone: 'immersive, literary, scene-driven' },
  { id: 'memoir_personal_story', shortLabel: 'Memoir', displayName: 'Memoir / Personal Story', description: 'Personal narrative storytelling.', recommendedMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'fiction_book_page', sourcePolicy: 'optional', defaultFormat: 'classic-novel', defaultTone: 'reflective, vivid, honest' },
  { id: 'childrens_illustrated_book', shortLabel: 'Illustrated', displayName: 'Children’s Illustrated Book', description: 'Short, image-led story pages.', recommendedMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'fiction_book_page', sourcePolicy: 'optional', defaultFormat: 'illustrated-story', defaultTone: 'warm and clear' },
  { id: 'marketing_story', shortLabel: 'Marketing', displayName: 'Marketing Story / Brand Book', description: 'Professional GTM and brand narrative.', recommendedMode: 'expert', allowedModes: ['expert', 'classical'], defaultSkill: 'marketing_book_page', sourcePolicy: 'recommended', defaultFormat: 'modern-editorial', defaultTone: 'professional, audience-aware, evidence-led' },
  { id: 'finance_explainer', shortLabel: 'Finance', displayName: 'Finance Explainer', description: 'Practical finance guidance and frameworks.', recommendedMode: 'expert', allowedModes: ['expert', 'classical'], defaultSkill: 'finance_book_page', sourcePolicy: 'recommended', defaultFormat: 'modern-editorial', defaultTone: 'precise, practical, careful' },
  { id: 'thought_leadership', shortLabel: 'Leadership', displayName: 'Business Thought Leadership', description: 'POV content for business leaders.', recommendedMode: 'expert', allowedModes: ['expert', 'classical'], defaultSkill: 'general_book_page', sourcePolicy: 'recommended', defaultFormat: 'modern-editorial', defaultTone: 'insightful and practical' },
  { id: 'case_study_collection', shortLabel: 'Case Study', displayName: 'Case Study Collection', description: 'Evidence-led case narratives.', recommendedMode: 'expert', allowedModes: ['expert', 'classical'], discouragedModes: ['classical'], defaultSkill: 'marketing_book_page', sourcePolicy: 'required', defaultFormat: 'modern-editorial', defaultTone: 'clear and concrete' },
  { id: 'educational_how_to', shortLabel: 'Guide', displayName: 'Educational / How-To Book', description: 'Instructional and learning-focused.', recommendedMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'general_book_page', sourcePolicy: 'optional', defaultFormat: 'classic-novel', defaultTone: 'clear and instructive' },
  { id: 'custom', shortLabel: 'Custom', displayName: 'Custom', description: 'Custom objective and tone.', recommendedMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'general_book_page', sourcePolicy: 'optional', defaultFormat: 'classic-novel', defaultTone: 'balanced' },
]

export const BOOK_TYPE_MAP = Object.fromEntries(BOOK_TYPES.map((b) => [b.id, b])) as Record<string, BookTypeConfig>
