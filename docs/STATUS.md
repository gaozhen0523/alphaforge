# Current Status

## Current Phase

Week 1 — End-to-End MVP

## Current Day

Day 3 — Factor Research: DONE

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

## Day 3 — Factor Research: DONE

今天完成完整的 factor research baseline workflow。

### Implemented

已实现并测试：

```text
compute_forward_return
cross_sectional_rank

compute_daily_ic
summarize_ic

assign_quantiles
compute_quantile_returns
summarize_quantile_returns

compute_factor_correlation
```

核心流程：

```text
Factor
→ Forward Return
→ Cross-Sectional Rank
→ Daily Spearman IC
→ IC / ICIR
→ Quantile Analysis
→ Factor Correlation
```

### Research Semantics

Forward return：

```text
forward_return(t, h) = price(t+h) / price(t) - 1
```

当前 `horizon` 表示 future available observations，而不是 strict exchange-calendar sessions。

Research timing 与 execution timing 明确分离：

```text
Day 3 Research:
factor(t) ↔ future return

Later Backtest:
signal(t) → position(t+1)
```

IC 是每个 date 独立计算的 cross-sectional Spearman correlation。ICIR 定义为 `mean daily IC / std daily IC`，不 annualize。

Quantiles 使用 `Q1 = lowest factor`、`Q5 = highest factor`。Daily quantile returns 先按 date × quantile 计算 cross-sectional equal-weight mean，再沿时间维度分析。

Top-minus-bottom 先逐日计算 `Q5(t) - Q1(t)`，再求时间均值。

Factor correlation 是 daily cross-sectional Spearman correlation 沿日期的 equal-weight mean，不是将五年 observations pooling 后直接计算。

### Production Research Run

Runner：`scripts/run_factor_research.py`

```text
uv run python scripts/run_factor_research.py
```

Production sanity：

```text
dataset rows: 352,215
symbol count: 300
date range: 2021-01-04 ~ 2025-12-31
forward_return non-null: 351,915
```

#### Momentum 20d

```text
valid IC days: 1,191

mean_ic: -0.01432920
ic_std: 0.22927143
icir: -0.06249886

q1_mean: 0.00057108
q2_mean: 0.00039494
q3_mean: 0.00036988
q4_mean: 0.00076541
q5_mean: 0.00086787

top_minus_bottom: 0.00029679
```

1-step predictive power 很弱，IC 接近 0，quantile profile 不单调，不能认为存在稳定 momentum alpha。

#### Reversal 5d

```text
valid IC days: 1,206

mean_ic: 0.02155429
ic_std: 0.20820682
icir: 0.10352345

q1_mean: 0.00079411
q2_mean: 0.00049486
q3_mean: 0.00055488
q4_mean: 0.00051615
q5_mean: 0.00058671

top_minus_bottom: -0.00020740
```

存在小幅 positive rank IC，但 quantile profile 不单调且 top-minus-bottom 为负。属于 weak / noisy reversal evidence，不是稳定 alpha。

#### Volatility 20d

```text
valid IC days: 1,191

mean_ic: -0.03175493
ic_std: 0.25518219
icir: -0.12444022

q1_mean: 0.00043811
q2_mean: 0.00023851
q3_mean: 0.00034920
q4_mean: 0.00069692
q5_mean: 0.00124019

top_minus_bottom: 0.00080208
```

Rank IC 为弱负，quantile profile 不单调且 extreme bucket behavior 较明显。IC 与 top-minus-bottom direction 不完全一致；目前没有证据表明存在 correctness bug，不继续增加 Day 3 diagnostics。

#### Factor Correlation

```text
                momentum_20d  reversal_5d  volatility_20d
momentum_20d        1.000000    -0.437732        0.164410
reversal_5d        -0.437732     1.000000       -0.030020
volatility_20d      0.164410    -0.030020        1.000000
```

Momentum / Reversal 中等负相关。Volatility 与另外两个 factor 的相关性较弱，提供相对不同的信息维度。

### Correctness Sanity

有效 IC days 与 lookback / forward-return timing 完全一致：

```text
Momentum / Volatility:
1212 - 20 - 1 = 1191

Reversal:
1212 - 5 - 1 = 1206
```

实际结果完全匹配。Paired observation counts 也与 factor lookback 和 terminal forward-return NaN 对齐，当前没有发现明显 factor / forward-return timing 或 alignment bug。

### Day 3 Final Conclusion

三个基础 factors 在当前 1-step close-to-close forward return 下 predictive power 较弱且 noisy，这是正常且接受的 baseline research result。

- 不做 parameter tuning 来改善结果。
- 不修改 factor definitions 追求漂亮 IC。
- 不继续增加 Day 3 diagnostics，除非以后出现明确 correctness evidence。
- 不把 Day 3 quantile forward return 当成 tradable strategy PnL。
- Day 3 的成果重点是正确、完整的 factor research workflow。

保持 `Correctness > Return`。

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

Day 4 — Portfolio

```text
factor
→ signal
→ target weights
```

范围：Weekly rebalance、long only、top quantile、equal weight。

Day 4 只负责 `signal / selection → target portfolio weights`，不要提前混入 execution、transaction cost、slippage 或 PnL；这些留给 Day 5。

开始 Day 4 时先讲完整 Portfolio flow、明确关键 semantics，再尽量一次 cohesive implementation 并统一 review，不再拆成大量“一函数一次 Codex”的任务。
