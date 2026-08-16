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

- Step 1 forward return：已实现 `forward_return(t, h) = price(t+h) / price(t) - 1`。
- Forward horizon 按各 symbol 的 future available observations 计数，不引入 exchange calendar。
- 计算按 symbol 隔离、按 date 升序执行，并恢复输入 index / row order；insufficient future observations 保留 NaN。
- Step 2 cross-sectional rank：按 date 对 available stocks 独立计算 percentile rank；NaN 保留，ties 使用 average rank。
- Step 3A daily IC：按 date 对 raw factor 与 raw forward return 的有效配对 observations 计算 Spearman correlation；不足 `min_obs` 或 correlation 未定义时保留 NaN。
- Step 3B IC summary / ICIR：基于 non-NaN daily IC 计算 arithmetic mean、sample standard deviation（`ddof=1`）和未年化 ICIR；标准差无定义或为零时 ICIR 保留 NaN。
- Step 4A quantile assignment：复用 cross-sectional percentile rank，按 `ceil(rank * n_quantiles)` 分组；Q1 为最低 factor，Qn 为最高 factor，ties 不拆分，missing factor 保留 missing quantile。
- Step 4B daily quantile returns：先按 date × quantile 对有效 forward returns 计算 cross-sectional equal-weight arithmetic mean；输出保留固定 Q1...Qn schema，缺失组合保持 NaN。
- Step 4C quantile return summary：对 daily quantile return matrix 按时间计算 arithmetic mean；top-minus-bottom 先逐日配对相减再求均值，不使用独立均值之差。
- Step 5 factor correlation：按 date 对 raw factors 计算 pairwise-valid Spearman correlation matrix，再沿时间对 daily matrices 等权求 arithmetic mean；NaN 不填零。
- Production factor research runner：已新增 `scripts/run_factor_research.py`，串联 production loader、三个 baseline factors、1-day forward return、IC/ICIR、quantile returns 和 factor correlation；真实数值结果等待在可用的 `uv` 环境中运行。

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

- Day 3 — Factor Research：本地运行 production runner 并记录第一版真实 research results。
