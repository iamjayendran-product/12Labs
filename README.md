# 12Labs Feedback RAG (MVP)

A minimal RAG (retrieval-augmented generation) app for collating and
querying customer/client feedback. This MVP uses mock transcripts
(`data/transcripts/`) simulating AI-voice-agent-conducted customer
interviews about a fictional 12Labs voice/audio product. Swap in real
transcripts later by dropping them into the same directory and re-running
ingestion.

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

This reads every transcript in `data/transcripts/`, chunks it, embeds the
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

Covers chunking logic, retrieval relevance (using the real local embedding
model against a small synthetic corpus), and the `/chat` API contract for
both backends (validation, missing-key/unreachable-server errors, and
mocked happy paths) — none of this requires Ollama running or an
`ANTHROPIC_API_KEY`.

## Project layout

```
data/transcripts/   mock customer feedback transcripts (JSON)
app/embeddings.py   local embedding model wrapper
app/vectorstore.py  Chroma wrapper
app/rag.py          retrieval + prompt/answer logic (Ollama or Claude backend)
app/main.py         FastAPI app (POST /chat, serves static/)
scripts/ingest.py   builds the vector store from data/transcripts/
static/index.html   chat UI
tests/               pytest suite (chunking, retrieval, API contract)
```
