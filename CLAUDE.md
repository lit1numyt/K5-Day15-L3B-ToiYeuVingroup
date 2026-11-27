# CLAUDE.md — notes for Claude Code in this repo

Hackathon submission (VinAI Talent, Track B — Healthcare). Team **Tôi Yêu Vingroup**, class **L3B**.
Project: **NurseFlow** — per-shift nurse work-assignment planner.

## Read these first
- [`AGENTS.md`](AGENTS.md) — **hard rules** (what the agent must NOT do). Always wins over this file.
- [`Problem-Gap-Solution.md`](Problem-Gap-Solution.md) — the full product vision (source of truth for the problem).
- [`spec.md`](spec.md) — the AI spec; §4 holds the committed slice.
- [`contribution-guide.md`](contribution-guide.md) — branch & commit rules (follow them).

## The slice (what the AI actually decides)
At the start of a shift, given the shift's nurse roster (skills + availability; an absent nurse is simply left out) and the shift's task list, the agent proposes a **draft shift plan** (skill-aware assignment, compatible-task grouping, protected breaks, no coverage violations) for the nurse-in-charge to approve. It does **not** auto-apply, make clinical decisions, or re-plan continuously mid-shift (MVP = plan at shift start only).

## Conventions
- **User-facing / product content → Vietnamese.** Chat with me can be English; code identifiers in English.
- **Git flow:** work on `feat/*|fix/*|docs/*|chore/*` off `develop`; `--no-ff` merge into `develop`; keep `develop` green (`python run.py check`) before merging to `main`. Never commit straight to `main`. **Atomic commits** — one logical change each.
- **Reviewer before `main`:** team leader Khoa (`lit1numyt`).
- **Don't fabricate** numbers, quotes, interviewees, survey data (per `AGENTS.md`). Unsourced numbers → mark *(tự ước tính)*.
- **Never edit** framework files (`run.py`, `codebase/tracing.py`, `eval/run_eval.py`, `cost/simulate.py`) or already-run outputs (`eval/run-*.csv`, `cost/simulate-*.csv`, `traces/*`), except filling `pass`/`ghi_chu`.
- Team code lives in `codebase/`: `agent.py` (main flow), `ai.py` (`call_model`, token from API usage — never estimate), `tools.py` (one `@tool` per fn). Stdlib-only; new deps → `requirements.txt`.

## Commands
`python run.py` · `python run.py check` · `python run.py eval --try` · `python run.py eval` · `python run.py score eval/run-N.csv` · `python run.py simulate`

## Checkpoints
CP1 track+problem (done, on `main`) · CP2 Fri 27/11 19:30 (lock "đạt" bar, ≥10 eval cases) · CP3 Sat 28/11 10:00 (real model, 20–30 cases) · CP4 Sat 28/11 14:30 (full spec §0–§10).
