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

## Known limitations

- No auth/RBAC yet.
- No full audit/replay yet.
- Source retrieval is keyword-based (embeddings can be added later).
- PDF export is still a professional demo level.
- Image understanding is metadata-only (no OCR/vision analysis by default).
