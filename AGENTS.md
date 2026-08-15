# AlphaForge Agent Instructions

AlphaForge is an interview-oriented Quant Developer project.

## Goal
Target roles:
1. Strategy / Research + Platform QD
2. Strategy / Research QD
3. Research Platform / Backtest / Data Infra QD

Core workflow:
Data → Factor → Signal → Portfolio → Execution → PnL → Metrics

## Priorities
- Correctness > strategy return.
- Quant + engineering, not pure notebook or normal backend.
- Keep factor / signal / position / trade semantics explicit.
- Prevent look-ahead bias.
- Prefer simple correct Python before optimization.
- Core logic belongs in src/, not notebooks.
- Add tests for critical financial logic.
- Keep experiments reproducible.

## Scope
Do not introduce without explicit approval:
- ML / Deep Learning / LLM / Agent
- HFT / order book / live trading
- complex optimizer / risk model
- distributed infrastructure
- unnecessary factors or dependencies

## Workflow
Before coding:
1. Read docs/PROJECT.md
2. Read docs/ROADMAP.md
3. Read docs/STATUS.md
4. Inspect existing code

After completing a task:
- Run relevant tests.
- Summarize changes.
- Update docs/STATUS.md when the day's work is finished.