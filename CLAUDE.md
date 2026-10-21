# CLAUDE.md — 12Labs PM OS

## What this is
- **12Labs RAG MVP** (`app/`, `static/index.html`, `scripts/ingest.py`): chat over customer-interview transcripts. Leave `/chat` and the chat page working.
- **PM OS** (`pmos/`, `static/pmos/`): turns customer + sales signals into a RICE-ranked Q1 2027 roadmap. 12Labs (fictional voice/audio AI product) is the first company; the pipeline is company-agnostic via `data/companies/<name>/`.

Pipeline: source files → `/derive-backlog` (Claude Code skill) → `derived/backlog.json` → overrides → RICE → scheduler → API/UI → `ROADMAP.md`.

## Commands
- Setup: `source .venv/bin/activate && pip install -r requirements-dev.txt && python -m playwright install chromium`
- Tests: `pytest` runs everything incl. Playwright e2e (starts uvicorn itself, isolated state); `pytest --ignore=tests/e2e` for unit/api only
- Validate data: `python -m pmos.validate --company 12labs`
- Run: `python scripts/ingest.py && uvicorn app.main:app --reload` → `/` chat, `/pmos/roadmap.html` roadmap

## Rules
- Python 3.9: no `X | Y` annotations, no `match`. Use `typing.Optional`.
- Minimal deps: prefer local/no-API-key options. Derivation runs in Claude Code, not via an API key.
- Superpowers workflow: plan in `docs/plans/` → TDD (test fails first) → verify before marking a feature done → one commit per feature, on `feat/pmos`.
- Mock data is invented. Review sites are theme references only; never copy their text.
- Commitments (contract deal-breakers) are pinned outside RICE and scheduled first. Reach is computed from data, never typed.
- Evidence quotes in `backlog.json` must appear verbatim in their source record (`pmos.validate` enforces).

## State and timestamps
- **App state:** `state/events.jsonl` (append-only, ISO-8601 UTC `ts`, `actor`, `type`, `payload`) and `state/snapshot.json`. Git-ignored. Write only through `pmos/state.py`.
- **Build state:** `STATE.md` — add a timestamped entry at the end of every session (done / in progress / next / blockers).
- **Features:** `FEATURES.md` — status changes only after verification passes; update its `updated` timestamp.
