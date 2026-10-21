# 12Labs Feedback RAG (MVP)

A minimal RAG (retrieval-augmented generation) app for collating and
querying customer/client feedback. This MVP uses mock transcripts
(`data/companies/12labs/voc/`) simulating AI-voice-agent-conducted customer
interviews about a fictional 12Labs voice/audio product. Swap in real
transcripts later by dropping them into the same directory and re-running
ingestion.

## PM OS — Q1 2027 roadmap (12Labs as the example company)

A reusable "PM operating system" built on the same data: customer and sales
signals go in, a RICE-ranked, capacity-aware Jan–Mar 2027 roadmap comes out.

```
sources (data/companies/12labs/)         voice of customer (51 interviews), CRM sales notes (32),
                                         Fireflies meetings (10), NPS/support (42), commitments (6)
   └─ /derive-backlog (Claude Code)  →   derived/backlog.json  (29 items, verbatim evidence quotes)
        └─ overrides (state/events.jsonl)  →  RICE  →  scheduler  →  UI + ROADMAP.md
```

- **Commitments** (contract deal-breakers) are pinned outside RICE and scheduled first, earliest deadline first.
- **Reach** is computed: ARR-weighted distinct accounts in an item's evidence. Impact, Confidence and Effort are Claude's suggestions; edit them in the UI (logged, and they survive a re-derive).
- **Capacity**: 3 mock squads × 16 person-weeks a month; items that don't fit land "below the line".
- **All data is mock**, invented for this demo (themes inspired by public voice-AI review complaints; no text copied).

```bash
pip install -r requirements-dev.txt && python -m playwright install chromium
uvicorn app.main:app --reload     # then open /pmos/roadmap.html (also /pmos/backlog.html, /pmos/sources.html)
python -m pmos.validate --company 12labs --log-derived   # check backlog.json quotes + commitment coverage
python -m pmos.export --company 12labs                   # regenerate ROADMAP.md
```

Re-derive after the sources change by running `/derive-backlog` in Claude Code
(see `.claude/skills/derive-backlog/SKILL.md`). The current output is in
[ROADMAP.md](ROADMAP.md). Project conventions: [CLAUDE.md](CLAUDE.md),
feature status: [FEATURES.md](FEATURES.md), build log: [STATE.md](STATE.md).

## Stack

- **Embeddings**: local `sentence-transformers` (`all-MiniLM-L6-v2`) — no API key needed
- **Vector store**: [Chroma](https://www.trychroma.com/), embedded/local, persisted to `chroma_db/`
- **Generation**: local by default via [Ollama](https://ollama.com) (`qwen2.5:7b-instruct-q4_K_M`),
  or the Anthropic Claude API — switchable via `GENERATION_BACKEND` in `.env`. No API key
  needed for the local path.
- **Backend**: FastAPI
- **Frontend**: single static HTML page (no build step)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

### Local generation (default — no API key needed)

```bash
brew install ollama
brew services start ollama          # runs Ollama in the background
ollama pull qwen2.5:7b-instruct-q4_K_M
```

`.env` already defaults to `GENERATION_BACKEND=ollama`, so no further config is needed.
Tested on a MacBook Air M4 / 16GB RAM: ~5-25s per answer depending on question complexity.

### Anthropic Claude instead

Set `GENERATION_BACKEND=anthropic` and `ANTHROPIC_API_KEY=...` in `.env`.

## Build the vector store

```bash
python scripts/ingest.py
```

This reads every transcript in `data/companies/12labs/voc/`, chunks it, embeds the
chunks locally, and writes them to `chroma_db/`. Re-run this any time
transcripts change.

## Run

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000 and ask questions like:

- "What do customers say about voice latency?"
- "Any complaints about pricing?"
- "What do customers like most?"

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

`pytest` also runs the Playwright browser tests in `tests/e2e/` (they start the
app on a free port with isolated state). Skip them with `pytest --ignore=tests/e2e`.
The unit tests cover the PM OS schema, RICE, scheduler, event log, validator,
API and export. The RAG tests cover chunking logic, retrieval relevance (using the real local embedding
model against a small synthetic corpus), and the `/chat` API contract for
both backends (validation, missing-key/unreachable-server errors, and
mocked happy paths) — none of this requires Ollama running or an
`ANTHROPIC_API_KEY`.

## Project layout

```
data/companies/12labs/voc/   mock customer feedback transcripts (JSON)
app/embeddings.py   local embedding model wrapper
app/vectorstore.py  Chroma wrapper
app/rag.py          retrieval + prompt/answer logic (Ollama or Claude backend)
app/main.py         FastAPI app (POST /chat, serves static/)
scripts/ingest.py   builds the vector store from data/companies/12labs/voc/
static/index.html   chat UI
pmos/               PM OS: schema, loaders, rice, scheduler, state (event log), validate, pipeline, api, export
static/pmos/        PM OS pages: sources, backlog (RICE), roadmap
.claude/skills/derive-backlog/   Claude Code skill that derives backlog.json from the sources
ROADMAP.md · CLAUDE.md · FEATURES.md · STATE.md   output, conventions, feature status, build log
tests/               pytest suite (RAG + PM OS) and tests/e2e (Playwright)
```
