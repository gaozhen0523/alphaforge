# AlphaForge Agent Instructions

## Before Every Task

1. Read `docs/PROJECT.md`, `docs/ROADMAP.md`, and `docs/STATUS.md`.
2. Inspect the relevant existing code and tests before making changes.

## Development Rules

- Correctness > Return.
- Follow the roadmap and avoid expanding scope without explicit approval.
- Keep factor, signal, position, trade, return, and PnL semantics explicit; prevent look-ahead bias.
- Put core logic in `src/`; use notebooks only for research and visualization.
- Implement correct Python first, profile second, and consider C++ only for a demonstrated hot path.
- Keep experiments reproducible and add tests for critical financial logic.

## Completion Rules

- Run relevant tests after changes.
- Update `docs/STATUS.md` after substantively completing a task.
- Keep the final response concise: report only changed files, tests, and unresolved issues.
