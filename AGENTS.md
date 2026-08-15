# AlphaForge Agent Instructions

## Project Principle

AlphaForge 是面向 Quant Developer 求职的 interview-oriented quant engineering project，不是 production SDK。

- Correctness > Return。
- Simplicity > Unnecessary Abstraction。
- 保证 quant correctness，但优先代码简洁、可读、可解释。
- Prefer the simplest implementation that clearly expresses the quant logic。
- 避免 over-engineering 和过度 defensive programming。
- 不需要针对大量不现实的外部输入编写复杂 validation。
- 避免不必要的 class hierarchy、framework、generic abstraction 和 helper layers。
- 只有明显改善 correctness、debuggability 或模块边界时才增加 abstraction。
- upstream 已保证的 contract，下游不要重复大量 validation。
- 如果 10–20 行直接实现能清楚表达 quant logic，不要扩展成复杂工程架构。
- 代码应方便用户自己阅读，并可在 QD interview 中逐段解释。
- 先实现简单、正确的 Python，再 profiling，再根据真实 bottleneck 考虑 C++。

## Before Every Task

1. 读取 `docs/PROJECT.md`、`docs/ROADMAP.md` 和 `docs/STATUS.md`。
2. 修改前检查相关现有代码和 tests。

## Development Workflow

- 遵循 roadmap；未经明确批准不得扩大 scope。
- 明确 factor、signal、position、trade、return 和 PnL 语义，防止 look-ahead bias（前视偏差）。
- 核心逻辑放在 `src/`；notebooks 只用于研究和可视化。
- 保持实验可复现。
- tests 聚焦真正重要的 formulas、factor timing、look-ahead bias、alignment、NaN semantics 和 key invariants；不追求大量 edge cases 或 coverage 数字。

## Python Environment

- 使用 `uv` 管理 Python environment。
- Python command 优先使用 `uv run ...`。
- 不直接使用 `pip install`。
- 如果 Codex sandbox 无法运行 `uv`，不得修改或重建本地 environment；只报告限制，并给出用户需要执行的准确 `uv run ...` 命令。

## Documentation Language

- 项目解释、设计理由、计划和状态以中文为主，保留自然的 English technical terms；必要时在术语首次出现时附中文解释。
- module / class / function / variable / CLI command 使用英文。
- formulas 保持标准数学或英文表达。
- code comments 和 docstrings 使用英文。

## Completion Rules

- 修改后运行相关 tests。
- 实质性完成任务后更新 `docs/STATUS.md`。
- 最终回复保持简洁，只报告 changed files、tests 和 unresolved issues。
