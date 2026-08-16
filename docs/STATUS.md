# Current Status

## Current Phase

Week 1 — End-to-End MVP

## Current Day

Day 2 — Factors

## Day 1 — Data: DONE

- Full test suite：71 passed。
- Frozen universe：CSI300；`snapshot_date = 2026-08-14`；300 symbols。
- Production dataset：`data/processed/ohlcv_hfq.parquet`。
- Actual date range：2021-01-04 ~ 2025-12-31。
- Dataset：352,215 rows；1,212 trading days；300 symbols；unbalanced panel。
- Acquisition：requested=300；succeeded=300；failures=0。
- Data quality：duplicate `(date, symbol)` = 0；raw OHLCV NaN = 0。
- Data semantics：price convention = `hfq`；volume unit = shares。
- Week 1 使用 frozen static CSI300 universe；已明确记录 survivorship / membership bias limitation。

## 当前工作

Day 2 — Factors：基础 factor engine 已实现，等待本地完整测试确认。

## Day 2 — Factors

- 实现 `momentum(df, window=20)`：`close_t / close_(t-window) - 1`。
- 实现 `reversal(df, window=5)`：negative trailing return。
- 实现 `volatility(df, window=20)`：1-day close return 的 rolling sample standard deviation；不 annualize。
- Timing semantics：factor(t) 仅使用 `<= t` 数据；factor 层不做 execution shift。
- 所有 time-series calculation 按 symbol 隔离并按 date ascending 计算；输出恢复到输入 index。
- lookback 不足保留 NaN。
- `window <= 0` 明确拒绝，避免 negative shift 引入 look-ahead bias。
- 添加 known values、sign、volatility、warm-up、symbol isolation、shuffled order 和 index alignment tests。
- Codex 命令行环境无法运行项目 `uv`，完整 test suite 尚待本地执行。

## Next

- 本地运行 `uv run pytest`。
- 测试通过后进入 Day 3 — Factor Research。
