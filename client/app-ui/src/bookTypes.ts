export type BookTypeConfig = {
  id: string
  displayName: string
  description: string
  defaultMode: 'classical' | 'expert'
  allowedModes: Array<'classical' | 'expert'>
  defaultSkill: string
  sourcePolicy: 'optional' | 'recommended' | 'required'
  defaultFormat: 'classic-novel' | 'illustrated-story' | 'modern-editorial'
  defaultTone: string
}

export const BOOK_TYPES: BookTypeConfig[] = [
  { id: 'fiction_novel', displayName: 'Fiction Novel', description: 'Long-form narrative fiction, scenes and characters.', defaultMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'fiction_book_page', sourcePolicy: 'optional', defaultFormat: 'classic-novel', defaultTone: 'immersive, literary, scene-driven' },
  { id: 'memoir_personal_story', displayName: 'Memoir / Personal Story', description: 'Personal narrative storytelling.', defaultMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'fiction_book_page', sourcePolicy: 'optional', defaultFormat: 'classic-novel', defaultTone: 'reflective, vivid, honest' },
  { id: 'childrens_illustrated_book', displayName: 'Children’s Illustrated Book', description: 'Short, image-led story pages.', defaultMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'fiction_book_page', sourcePolicy: 'optional', defaultFormat: 'illustrated-story', defaultTone: 'warm and clear' },
  { id: 'marketing_story', displayName: 'Marketing Story / Brand Book', description: 'Professional GTM and brand narrative.', defaultMode: 'expert', allowedModes: ['expert', 'classical'], defaultSkill: 'marketing_book_page', sourcePolicy: 'recommended', defaultFormat: 'modern-editorial', defaultTone: 'professional, audience-aware, evidence-led' },
  { id: 'finance_explainer', displayName: 'Finance Explainer', description: 'Practical finance guidance and frameworks.', defaultMode: 'expert', allowedModes: ['expert', 'classical'], defaultSkill: 'finance_book_page', sourcePolicy: 'recommended', defaultFormat: 'modern-editorial', defaultTone: 'precise, practical, careful' },
  { id: 'thought_leadership', displayName: 'Business Thought Leadership', description: 'POV content for business leaders.', defaultMode: 'expert', allowedModes: ['expert', 'classical'], defaultSkill: 'marketing_book_page', sourcePolicy: 'recommended', defaultFormat: 'modern-editorial', defaultTone: 'insightful and practical' },
  { id: 'case_study_collection', displayName: 'Case Study Collection', description: 'Evidence-led case narratives.', defaultMode: 'expert', allowedModes: ['expert'], defaultSkill: 'marketing_book_page', sourcePolicy: 'required', defaultFormat: 'modern-editorial', defaultTone: 'clear and concrete' },
  { id: 'educational_how_to', displayName: 'Educational / How-To Book', description: 'Instructional and learning-focused.', defaultMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'fiction_book_page', sourcePolicy: 'optional', defaultFormat: 'classic-novel', defaultTone: 'clear and instructive' },
  { id: 'custom', displayName: 'Custom', description: 'Custom objective and tone.', defaultMode: 'classical', allowedModes: ['classical', 'expert'], defaultSkill: 'fiction_book_page', sourcePolicy: 'optional', defaultFormat: 'classic-novel', defaultTone: 'balanced' },
]

export const BOOK_TYPE_MAP = Object.fromEntries(BOOK_TYPES.map((b) => [b.id, b])) as Record<string, BookTypeConfig>
