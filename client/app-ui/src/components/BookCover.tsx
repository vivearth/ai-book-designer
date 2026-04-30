import { resolveGeneratedCoverUrl, resolveUploadUrl } from '../api'
import type { Book } from '../types'
import { GeneratedCover } from './GeneratedCover'

function fitCoverTitle(title: string): { text: string; sizeClass: string } {
  const clean = (title || 'Untitled').trim().replace(/\s+/g, ' ')
  const sizeClass = clean.length > 72 ? 'cover-title--sm' : clean.length > 44 ? 'cover-title--md' : 'cover-title--lg'
  const compact = clean.length > 96 ? `${clean.slice(0, 93).trimEnd()}…` : clean
  return { text: compact, sizeClass }
}

export function BookCover({ book }: { book: Book }) {
  const { text: displayTitle, sizeClass } = fitCoverTitle(book.title || 'Untitled')
  if (book.cover_source === 'uploaded' && book.cover_image_filename) {
    return <div className="book-cover-shell"><img className="book-cover-image" src={resolveUploadUrl(book.cover_image_filename)} alt={book.cover_original_filename || book.title} /><div className={`book-cover-title ${sizeClass}`}>{displayTitle}</div></div>
  }

  if (book.id) {
    return <div className="book-cover-shell"><img className="book-cover-image" src={resolveGeneratedCoverUrl(book.id)} alt={`${book.title} cover`} /><div className={`book-cover-title ${sizeClass}`}>{displayTitle}</div></div>
  }

  return <GeneratedCover book={book} />
}
