# Current Status

## Current Phase

Week 1 — End-to-End MVP

## Current Day

Day 4 — Portfolio: DONE

## Day 1 — Data: DONE

- Frozen universe：CSI300 current-membership snapshot（`2026-08-14`），300 symbols；Week 1 接受 survivorship / membership bias limitation。
- Production dataset：`data/processed/ohlcv_hfq.parquet`；2021-01-04 ~ 2025-12-31；352,215 rows；1,212 trading days；unbalanced panel。
- Acquisition：requested=300，succeeded=300，failures=0。
- Data quality：duplicate `(date, symbol)` = 0；raw OHLCV NaN = 0。
- Data semantics：`hfq` adjusted OHLC，volume unit = shares。

## Day 2 — Factors: DONE

- Implemented：20-day momentum、5-day reversal、20-day volatility。
- Timing：`factor(t)` 只使用截至 t 的信息；factor layer 不做 execution shift，后续 backtest 执行 `signal(t) → position(t+1)`。
- 按 symbol 隔离、按 date 升序计算，并恢复输入 index / row order；insufficient lookback 保留 NaN。
- Production sanity：momentum NaN = 6,000；reversal NaN = 1,500；volatility NaN = 6,000；inf count = 0。
- Extreme values 与真实 high-volatility / limit-up events 一致，未发现明显 factor bug。

## Day 3 — Factor Research: DONE

- Implemented：forward return、cross-sectional rank、daily Spearman IC、ICIR、quantile assignment/returns/summary、mean daily factor correlation。
- Workflow：`Factor → Forward Return → Rank → IC / ICIR → Quantile Analysis → Factor Correlation`。
- Forward return：`price(t+h) / price(t) - 1`；`horizon` 表示 future available observations，不引入 exchange calendar。
- Research timing：`factor(t) ↔ future return`；与后续 `signal(t) → position(t+1)` execution timing 分离。
- ICIR 不 annualize；quantile return 先做 daily cross-sectional equal-weight mean；top-minus-bottom 先逐日 `Q5-Q1` 再求时间均值。
- Factor correlation 先按 date 计算 cross-sectional Spearman matrix，再对 dates 等权平均，不 pool 五年 stock observations。

Production runner：

```text
uv run python scripts/run_factor_research.py
```

Production sanity：352,215 rows；300 symbols；2021-01-04 ~ 2025-12-31；forward return non-null = 351,915。

### IC Summary

| Factor | Valid IC days | Mean IC | IC Std | ICIR |
|---|---:|---:|---:|---:|
| Momentum 20d | 1,191 | -0.01432920 | 0.22927143 | -0.06249886 |
| Reversal 5d | 1,206 | 0.02155429 | 0.20820682 | 0.10352345 |
| Volatility 20d | 1,191 | -0.03175493 | 0.25518219 | -0.12444022 |

### Quantile Return Summary

| Factor | Q1 Mean | Q2 Mean | Q3 Mean | Q4 Mean | Q5 Mean | Top−Bottom |
|---|---:|---:|---:|---:|---:|---:|
| Momentum 20d | 0.00057108 | 0.00039494 | 0.00036988 | 0.00076541 | 0.00086787 | 0.00029679 |
| Reversal 5d | 0.00079411 | 0.00049486 | 0.00055488 | 0.00051615 | 0.00058671 | -0.00020740 |
| Volatility 20d | 0.00043811 | 0.00023851 | 0.00034920 | 0.00069692 | 0.00124019 | 0.00080208 |

### Mean Daily Factor Correlation

```text
                momentum_20d  reversal_5d  volatility_20d
momentum_20d        1.000000    -0.437732        0.164410
reversal_5d        -0.437732     1.000000       -0.030020
volatility_20d      0.164410    -0.030020        1.000000
```

### Conclusion

- 三个 factors 对 1-step close-to-close forward return 的 predictive power 均较弱且 noisy；quantile profiles 不单调，不构成稳定 alpha 证据。
- Momentum / Reversal 中等负相关；Volatility 与两者相关性较弱，提供不同信息维度。
- Valid IC days 与 timing 完全一致：Momentum / Volatility `1212 - 20 - 1 = 1191`；Reversal `1212 - 5 - 1 = 1206`。未发现 factor / forward-return alignment bug。
- 不做 parameter tuning，不修改 baseline definitions，不把 quantile forward return 当作 tradable strategy PnL；保持 `Correctness > Return`。

## Day 4 — Portfolio: DONE

- Implemented：`factor → signal → target weights`；baseline 使用 `momentum_20d`，higher factor is better。
- Weekly rebalance：每个 calendar week 中 dataset 最后一个 global trading date；所有 symbols 共用同一套 decision dates，Friday 缺失时使用该周最后一个实际 trading date。
- Selection / weighting：每个 rebalance date 独立使用 Day 3 quantile semantics；factor 非 NaN 的 Q5 stocks 做 long-only equal weight，其他 stocks 为 0。
- Carry forward：signal / target weights 只在 weekly decision 更新，两个 decision dates 之间保持当前 target；首个 decision 前为 0。
- Timing：`factor(t) → signal / target(t)`，Day 4 不做 execution shift；target weight 是目标配置，不是 actual position，也不表示每日交易维持 equal weight。
- Day 5 才处理：`signal(t) → execution / position(t+1)`、weight drift、turnover、transaction cost、slippage、return 和 PnL。

## Known Limitations

- Frozen current-membership CSI300 universe 存在 survivorship / membership bias。
- Unbalanced panel 的 rolling/forward horizon 使用 available observations，而非 strict exchange-calendar sessions。
- Data provider 可能将当前 ticker identifier 回填到历史 observations。

## Next — Day 5: Backtest

实现完整的 `position → turnover → cost → return → PnL` flow，并明确执行 `signal(t) → position(t+1)`，避免 look-ahead bias。
