# Current Status

## Current Phase

Week 1 — End-to-End MVP

## Current Day

Day 3 — Factor Research

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

Day 3 — Factor Research

## Day 2 — Factors: DONE

- Implemented：20-day momentum、5-day reversal、20-day volatility。
- Factor timing：`factor(t)` 使用截至 t 的信息；factor layer 内不做 execution shift；后续 backtest 强制执行 `signal(t) → position(t+1)`。
- Calculations 按 symbol 隔离、按时间顺序计算，并恢复到输入 index。
- Insufficient lookback 保留 NaN。
- Production sanity check（`ohlcv_hfq.parquet`）：352,215 rows；300 symbols；momentum NaN = 6,000；reversal NaN = 1,500；volatility NaN = 6,000；所有 factors 的 inf count = 0。
- Extreme values 已人工检查，表现与真实 high-volatility / limit-up market events 一致，未发现明显 factor bug。

### Known Limitations — Later Data Quality Work

1. 当前 unbalanced panel 的 rolling window 使用 previous available observations，而不是 strict exchange-calendar sessions。
2. ticker 变更后，data provider 可能将当前 ticker identifier 回填到历史 observations。

## Next

- Day 3 — Factor Research：cross-sectional rank、forward return、IC、ICIR 和 quantile analysis。
