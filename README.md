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

- CPU-only / 8GB RAM: `qwen2.5:3b-instruct` or `llama3.2:3b`
- Better quality with more RAM/CPU: `qwen3:8b`
- Large models only if hardware allows: `qwen2.5:14b-instruct`

The app uses **two-pass generation** (plan beats, then prose) for stronger page-level quality without paid APIs or fine-tuning. For slower machines, set `LLM_FAST_MODE=true` to run one-pass generation.

### CPU-friendly Ollama settings

- `OLLAMA_TIMEOUT_SECONDS=300`
- `OLLAMA_NUM_CTX=2048`
- `OLLAMA_NUM_PREDICT=220-320`
- `LLM_FAST_MODE=true` (recommended on small GPUs/CPU-only)
- `LLM_TWO_PASS_ENABLED=false` (recommended for faster demo runs)
- Nginx API proxy timeout is set to `300s` in `client/app-ui/nginx.conf`

### Troubleshooting: Ollama 500 after 2 minutes

Symptom in Ollama logs:

- `POST /api/generate 500 2m0s`

Why this happens:

- Model may be loaded, but CPU-only generation exceeded the request timeout.
- `qwen3:8b` can be slow on CPU-only Docker with ~8GB RAM.
- Two-pass generation may call the model multiple times per page.

How to fix:

1. Use a smaller model (`qwen2.5:3b-instruct` / `llama3.2:3b`).
2. Increase `OLLAMA_TIMEOUT_SECONDS`.
3. Set `LLM_FAST_MODE=true`.
4. Reduce `OLLAMA_NUM_CTX` and/or `OLLAMA_NUM_PREDICT`.
5. Set `OLLAMA_STREAM=true` for long-running generation.
6. Run Ollama on host/GPU if available.
7. Ensure frontend proxy timeout is long enough (`300s` in this repo).

Useful commands:

```bash
docker exec -it book_designer_ollama ollama list
docker exec -it book_designer_ollama ollama pull qwen2.5:3b-instruct
docker compose --profile llm up --build
```

### Ollama warmup for first-request latency

When running with `--profile llm`, compose starts an `ollama-warmup` service that:

1. waits for `/api/tags`
2. sends a tiny warmup `/api/generate` request
3. keeps model alive for demo usage

You can also run warmup manually:

```bash
./scripts/warmup_ollama.sh
```

Environment variables supported:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_WARMUP_TIMEOUT_SECONDS`
- `OLLAMA_KEEP_ALIVE`

### Future improvement (TODO)

Long-running generation should eventually move to async jobs (`POST /generate-jobs`, `GET /generate-jobs/{id}`) to avoid request/timeout coupling entirely.

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

## Typesetting-first MVP flow

The studio now supports both content generation and PRD-native typesetting selection:

- You can still generate page text with existing skills in Classical or Expert mode.
- You can also paste/provide page-level text + images and use **Generate Layout Options** without rewriting text.
- For each page, the app generates **two layout options** (Option A / Option B), shows them side-by-side, and lets you select one.
- Selecting an option copies that option into the page's active `layout_json`, which is then used by preview and PDF export.

Current MVP constraints:

- No drag/drop freeform editing yet.
- Layout options are deterministic structured variants, with optional AI-assisted rationale when available.
- Global style consistency across all pages can be improved further in future iterations.
