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

Day 2 — Factors

## Next

- 20-day Momentum
- 5-day Reversal
- 20-day Volatility
- unified factor API / timing semantics
