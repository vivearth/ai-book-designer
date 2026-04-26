import { resolveGeneratedCoverUrl, resolveUploadUrl } from '../api'
import type { Book } from '../types'
import { GeneratedCover } from './GeneratedCover'

export function BookCover({ book }: { book: Book }) {
  if (book.cover_source === 'uploaded' && book.cover_image_filename) {
    return <img className="book-cover-image" src={resolveUploadUrl(book.cover_image_filename)} alt={book.cover_original_filename || book.title} />
  }

  if (book.id) {
    return <img className="book-cover-image" src={resolveGeneratedCoverUrl(book.id)} alt={`${book.title} cover`} />
  }

  return <GeneratedCover book={book} />
}
