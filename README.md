# AI Book Designer POC

A rapid-development proof of concept for a web application that helps users design long-form books page by page. The product captures raw text and images, maintains structured book memory, generates coherent page content, suggests layout metadata, and exports a simple PDF.

## Repository layout

```text
book_designer_poc/
├── client/
│   └── app-ui/              # React + Vite UI
├── server/
│   └── app/                 # FastAPI backend
│       ├── api/             # HTTP routes
│       ├── core/            # config + database
│       ├── engines/         # context, memory, LLM, layout, PDF engines
│       ├── models/          # SQLAlchemy models + Pydantic schemas
│       └── services/        # orchestration services
└── docker-compose.yaml
```

## What this POC demonstrates

- Create a book with title, genre, tone, audience, and style guide.
- Add pages one by one with raw user input.
- Upload images against a page.
- Generate page content using a controlled context packet.
- Maintain book-level memory: summary, characters, locations, timeline, rules, and unresolved threads.
- Generate layout JSON for each page.
- Export approved/generated pages to PDF.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open the app:

```text
http://localhost:8080
```

Backend health:

```text
http://localhost:8000/health
```

## Optional local LLM with Ollama

By default, the POC runs with `MODEL_PROVIDER=mock`, so the product works without downloading any model.

To run with Ollama:

```bash
docker compose --profile llm up --build
```

Then pull a model inside the Ollama container:

```bash
docker exec -it book_designer_ollama ollama pull qwen3:8b
```

Update `.env`:

```text
MODEL_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b
```

Restart:

```bash
docker compose --profile llm up --build
```

## Backend concept

The backend does not send all 500 pages to the model. Instead, it builds a compact context packet using:

1. Book memory
2. Chapter/current page state
3. Recent pages
4. Relevant user input
5. Layout constraints

The core generation flow is:

```text
User page input
→ store raw input
→ build context packet
→ generate page text
→ validate/update book memory
→ generate layout JSON
→ store result
→ export PDF when needed
```

## Important POC limitations

- PDF layout is intentionally simple and uses ReportLab.
- Memory extraction is heuristic in mock mode and LLM-assisted in Ollama mode.
- Image understanding is placeholder-based. The backend stores images and captions but does not yet run vision models.
- No authentication is included.
- No background queue is included yet; generation happens inside API calls.

## Suggested next steps

1. Add user accounts and book ownership.
2. Add chapter entities instead of deriving chapter by page number.
3. Add pgvector for semantic retrieval from older pages.
4. Add background jobs for generation and PDF export.
5. Add richer page layout templates.
6. Add image captioning with a local vision model or multimodal provider.
7. Add continuity validation as a separate review step before approval.
