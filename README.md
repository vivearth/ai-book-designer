# AI Book Designer — Professional Content Studio

This project evolves the original AI-assisted book designer POC into a **professional content-to-book studio** for marketing, finance, and advisory workflows.

## Core workflow

1. Create a professional project.
2. Upload/paste source content (notes, markdown, PDFs, images).
3. Process sources into chunks.
4. Generate source-grounded pages with professional writing skills.
5. Review quality flags and used source references.
6. Preview and export a polished PDF draft.

## Architecture (current)

- **Project**: objective, audience, domain direction.
- **BrandProfile**: tone/rules for writing behavior.
- **FormatProfile**: reusable layout and export defaults.
- **Source Library**: `SourceAsset` + `SourceChunk`.
- **Skills**:
  - `marketing_book_page`
  - `finance_book_page`
  - `layout_composition`
  - `content_quality`
- **Book/Page** generation with project + source context.

## Run

### Docker

```bash
docker compose build
docker compose up
```

### Frontend build

```bash
cd client/app-ui
npm install
npm run build
```

### Backend tests

```bash
pip install -r server/requirements.txt
PYTHONPATH=server pytest server/tests -q
```

## Skills model

A **Skill** is a reusable capability. Output varies by project context (sources, direction, brand profile, format profile), not by one-off UI prompt hacks.

## Local model routing and quality (Ollama)

Generation quality depends heavily on local model choice. The app supports per-skill model routing:

- `FICTION_LLM_MODEL` → fiction pages
- `MARKETING_LLM_MODEL` → marketing pages
- `FINANCE_LLM_MODEL` → finance pages
- `GENERAL_LLM_MODEL` → general/educational pages
- `QUALITY_LLM_MODEL` → quality tasks (future-safe route)
- fallback order: skill model → `DEFAULT_LLM_MODEL` → `OLLAMA_MODEL`

Recommended local models:

- `qwen2.5:14b-instruct` (strong default for zero-cost local writing)
- `qwen2.5:32b-instruct` (if hardware allows)
- `mistral-small` (if available in your local setup)
- `llama3.1:8b` (baseline fallback only)

The app uses **two-pass generation** (plan beats, then prose) for stronger page-level quality without paid APIs or fine-tuning.

## Zero-cost quality improvement path

1. Choose a stronger local model.
2. Use skill-specific prompt contracts.
3. Use source retrieval for professional books.
4. Keep quality checks enabled (repetition, leakage, domain/source relevance).
5. Collect approved pages as future training data.

### Optional future LoRA path (not implemented in this branch)

Once enough pages are approved, export training pairs:

- Input: book type + page goal + source chunks + target words
- Output: approved final page

## Known limitations

- No auth/RBAC yet.
- No full audit/replay yet.
- Source retrieval is keyword-based (embeddings can be added later).
- PDF export is still a professional demo level.
- Image understanding is metadata-only (no OCR/vision analysis by default).

## Unified Book Studio flow

- Landing offers one path: continue an existing book or start a new book.
- New book uses a wizard:
  1. select book type
  2. choose classical/expert mode
  3. enter book details
  4. choose format
  5. expert mode: source setup + draft generation

### Manual verification checklist

- Expert mode creates a project first, then creates the book under that project.
- Expert source setup appears before workspace.
- Source upload and processing works from Source Library pane.
- Draft generation creates multiple pages for empty books (1..N).
- Cover button shows cover even when pages exist.
- Next page creates and selects page 2/page 3 correctly.
- User-selected format is preserved and not overwritten at submit time.
