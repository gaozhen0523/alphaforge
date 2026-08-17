# Current Status

## Current Phase

Week 1 — End-to-End MVP

## Current Day

Day 5 — Backtest: DONE

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

- Implemented：`Factor → Signal → Target Weights`；baseline 使用 `momentum_20d`，higher factor is better，long only、top quintile / Q5、equal weight。
- Core API：`build_long_only_top_quantile_portfolio(df, factor_col, n_quantiles=5)`。
- Weekly rebalance：使用 global market trading dates；每个 calendar week 最后一个实际 trading date 是 decision date，所有 symbols 共用同一套 schedule，不按每个 symbol 每 5 个 observations 重平衡。
- Cross-sectional selection：每个 decision date 独立复用 Day 3 quantile semantics；factor NaN 不参与 selection；ties 不强制拆分，因此 selected count 不要求严格等于 20%。
- Target weights：选中 `N` 只股票时各为 `1 / N`，未选中为 0；满足 long-only、selected equal weight 和 active cross-sectional weight sum = 1。
- Carry forward：`signal` / `target_weight` 只在 weekly decision 重新生成，两个 decision dates 之间保持当前 target；首个有效 target 前为 0。
- Portfolio panel：构造完整 `global date × symbol` panel；缺失 `(date, symbol)` observation 的 factor 为 NaN，并在新的 rebalance 时将其 target 正确归零，而不是延续旧 target。
- Timing boundary：`factor(t) → signal(t) → target_weight(t)` 到 Day 4 结束；不做 execution shift、turnover、transaction cost、slippage、return 或 PnL。
- `target_weight != actual portfolio weight`；carry-forward target 仅表示目标未改变，不表示每日重新交易维持 equal weight。Actual position、weight drift 和 execution 属于 Day 5。

Production runner：

```text
uv run python scripts/run_portfolio.py
```

Production sanity：

```text
rows: 363,600
symbols: 300
date range: 2021-01-04 to 2025-12-31

rebalance count: 256
first rebalance date: 2021-01-08
last rebalance date: 2025-12-31

selected count on rebalance dates (min/median/max): 0/59/60
target weight (min/max): 0/0.01851852
negative weight count: 0
active cross-sectional weight sum (min/max): 1/1
non-unit active dates: 0
```

Portfolio panel 为 `1,212 trading dates × 300 symbols = 363,600 rows`。Selected count minimum 为 0，来自 `momentum_20d` 初始 lookback 尚未形成有效 factor 的早期 rebalance dates，不是 portfolio bug。

Local tests：

```text
uv run pytest tests/test_portfolio.py tests/test_quantiles.py tests/test_ranking.py
38 passed in 0.69s
```

Tests 覆盖 cross-sectional Q5、global weekly schedule、Friday 缺失、非 rebalance 日不重新选股、portfolio invariants、NaN factor exclusion，以及 symbol 在新 decision date 缺行时 target 正确归零。

## Day 5 — Backtest: DONE

- Implemented：`target → execution → actual position → weight drift → turnover → cost → return → NAV`；core API 为 `run_backtest(market_data, portfolio, transaction_cost_bps=5.0, slippage_bps=5.0)`，返回 position panel 和 daily portfolio summary。
- Timing：decision date `t` 的 target 在下一 global trading date close 执行；当日先由 previous post-trade weights 承担 close-to-close return，再 drift 为 pre-trade weights，最后执行 delayed target。最后一个 decision 后若无下一 global date，则不执行。
- Target / actual：`target_weight != actual portfolio weight`。Carry-forward target 不触发 daily rebalance；只有显式 `is_rebalance` 延迟形成的 execution event 才交易。即使连续 decision targets 相同，也会从当时 drifted pre-trade weights 调回 target。
- Drift：stock weights 按 `w_i(1+r_i)/(1+r_p)` 漂移，cash weight 隐式为 `1-sum(stock weights)`，cash return 为 0；支持初始 cash、fully invested、portfolio-to-cash 和 cash-to-portfolio。
- Trade / turnover：`gross_traded_weight = sum(abs(stock trade weights))`；`turnover` 为包含 cash leg 的 half-L1。Cost 使用 gross stock traded notional，而非 turnover。
- Cost / NAV：transaction cost 和 slippage 均为 linear bps model；`net_return=(1+gross_return)(1-total_cost)-1`，`nav(t)=nav(t-1)(1+net_return(t))`，`cumulative_pnl=nav-1`。
- Missing observation：在完整 global dates 上对每个 symbol 只用过去 observed close 做 forward fill；缺失 observation 当日 return 为 0，下次真实 close 体现累计变化，绝不 backfill future price。
- Limitation：Week 1 假设可以按 idealized marked close 执行，不模拟 suspension 无法成交、limit up/down、bid/ask、volume participation、liquidity 或 market impact。

Production runner：

```text
uv run python scripts/run_backtest.py
```

Production sanity result：待用户在本地 `uv` environment 执行后确认；Codex sandbox 未运行，不伪造 rows、cost 或 NAV 结果。

Local tests command：

```text
uv run pytest tests/test_backtest.py tests/test_portfolio.py
```

Local test result：待用户本地执行后确认；Codex sandbox 未运行 `uv` tests。

## Known Limitations

- Frozen current-membership CSI300 universe 存在 survivorship / membership bias。
- Unbalanced panel 的 rolling/forward horizon 使用 available observations，而非 strict exchange-calendar sessions。
- Data provider 可能将当前 ticker identifier 回填到历史 observations。

## Next — Day 6: Analytics & Tests

实现 Sharpe、annualized return / volatility、max drawdown 等 analytics；Day 5 不提前加入这些 metrics。
