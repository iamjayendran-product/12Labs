# FEATURES — PM OS

Status: `planned` | `in-progress` | `done`. A feature is `done` only after its acceptance criteria were verified by a command run.

| ID | Feature | Acceptance criteria | Status | Updated (UTC) |
|----|---------|---------------------|--------|---------------|
| F-01 | Project scaffolding | CLAUDE.md, FEATURES.md, STATE.md, docs/plans exist; pytest-playwright installed | done | 2026-10-21T11:20:16Z |
| F-02 | Data layout + company config | `data/companies/12labs/` holds voc + company.json; `ingest.py` reads it, old path still works; existing tests green | done | 2026-10-21T11:20:16Z |
| F-03 | Mock data + schemas | CRM (~30), Fireflies (~10), NPS/support (~40), commitments (~6), ~15 new interviews; all validate; ~12 planted themes | done | 2026-10-21T11:20:16Z |
| F-04 | State / event log | append-only events with ISO timestamps; snapshot replay; overrides survive re-derive | planned | |
| F-05 | RICE engine | Reach = sum of clamp(arr/median,1,3) over distinct accounts; score = R·I·C/E; overrides applied | planned | |
| F-06 | Scheduler | commitments first by due month; capacity per squad-month; dependencies; at-risk and below-the-line | planned | |
| F-07 | /derive-backlog skill + validator | skill writes backlog.json; validator checks verbatim quotes and commitment coverage | planned | |
| F-08 | API router | endpoints under `/api/pmos/*` per plan; mounted in `app/main.py`; chat unaffected | planned | |
| F-09 | UI pages | Sources, Backlog/RICE (editable), Roadmap (Jan/Feb/Mar) | planned | |
| F-10 | Markdown export | `ROADMAP.md` with 3 months, themes, committed, quotes, below the line | planned | |
| F-11 | Playwright e2e | 4 flows from plan pass | planned | |
| F-12 | README + final verification | README documents PM OS; full suite green | planned | |
