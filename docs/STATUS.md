# Current Status

## Current Phase

Week 2 — Resume-Ready MVP

## Current Day

Day 8 — Data Quality: NEXT

## Day 1 — Data: DONE

- Core APIs：`normalize_ohlcv`、`validate_ohlcv`、`MarketDataLoader`，canonical schema 为 `date / symbol / OHLCV`，按 `date, symbol` 排序且不自动补行。
- Universe：CSI300 current-membership snapshot（`2026-08-14`），300 symbols；acquisition `300/300` succeeded，failures `0`。
- Production data：`data/processed/ohlcv_hfq.parquet`，2021-01-04 ~ 2025-12-31，352,215 rows，1,212 global trading dates，unbalanced panel。
- Data quality / semantics：duplicate `(date, symbol)=0`，raw OHLCV NaN `=0`；`hfq` adjusted OHLC，volume unit = shares。

## Day 2 — Factors: DONE

- Core APIs：`momentum`、`reversal`、`volatility`；baseline windows 为 20 / 5 / 20 trading observations。
- Timing：`factor(t)` 只使用截至 `t` 的 observed history；按 symbol 隔离、按 date 升序计算，factor layer 不做 execution shift，insufficient lookback 保留 NaN。
- Production sanity：momentum NaN `=6,000`，reversal NaN `=1,500`，volatility NaN `=6,000`，inf count `=0`；未发现 factor timing / alignment bug。

## Day 3 — Factor Research: DONE

- Core APIs：`compute_forward_return`、`cross_sectional_rank`、`compute_daily_ic` / `summarize_ic`、quantile assignment / returns / summary、`compute_factor_correlation`。
- Timing / semantics：forward return 为 `price(t+h)/price(t)-1`，`horizon` 使用 future available observations；daily rank、IC、quantile 和 correlation 均按 date 做 cross-sectional calculation，不 pool 全历史 observations。
- Production sanity：352,215 rows，300 symbols，2021-01-04 ~ 2025-12-31，1-step forward return non-null `=351,915`。

| Factor | Valid IC days | Mean IC | ICIR | Q5−Q1 mean |
|---|---:|---:|---:|---:|
| Momentum 20d | 1,191 | -0.01432920 | -0.06249886 | 0.00029679 |
| Reversal 5d | 1,206 | 0.02155429 | 0.10352345 | -0.00020740 |
| Volatility 20d | 1,191 | -0.03175493 | -0.12444022 | 0.00080208 |

- Conclusion：predictive power 较弱且 noisy，quantile profiles 不单调，不构成稳定 alpha 证据；Momentum / Reversal mean daily correlation 约 `-0.438`，Volatility 与两者相关性较弱。保持 baseline definitions，不做 parameter tuning 或 data snooping。
- Production runner：`uv run python scripts/run_factor_research.py`。

## Day 4 — Portfolio: DONE

- Core API：`build_long_only_top_quantile_portfolio(df, factor_col, n_quantiles=5)`；baseline 为 `momentum_20d`、long only、Q5、equal weight。
- Schedule / selection：每个 calendar week 最后一个 global trading date 是统一 decision date；factor NaN 不参与 selection，ties 不强拆，因此 selected count 不要求严格等于 20%。
- Timing contract：`factor(t) → signal(t) → target_weight(t)`；signal / target 仅在 decision date 更新，其余日 carry forward。`target_weight` 是目标而非 actual weight，carry forward 不表示 daily rebalance。
- Panel contract：完整 `global date × symbol`；missing observation 的 factor 保持 NaN，并在新 decision 上正确生成该 symbol 的新 target。
- Production sanity：363,600 rows（1,212 dates × 300 symbols），256 decisions；selected count min/median/max `0/59/60`，active weight sum `1`，negative weights `0`。最早 warm-up decisions selected count 为 0 属于预期行为。
- Verified tests：`uv run pytest tests/test_portfolio.py tests/test_quantiles.py tests/test_ranking.py` → `38 passed in 0.69s`。
- Production runner：`uv run python scripts/run_portfolio.py`。

## Day 5 — Backtest: DONE

- Core API：`run_backtest(market_data, portfolio, transaction_cost_bps=5.0, slippage_bps=5.0)`，返回完整 position panel 和 one-row-per-date daily summary。
- Timing contract：decision date `t` 的 target 在下一 global trading date close 执行。每日顺序为 previous post-trade weights → 当日 close-to-close return → drifted pre-trade weights → delayed execution → cost → net return / NAV；新 target 不获得 execution close 之前已经发生的收益。
- Execution contract：仅显式 `is_rebalance` 产生 delayed execution event；即使连续 targets 相同，也从当时 drifted pre-trade weights 调回 target。最后一个 decision 后无下一 global date，因此 `256 decisions → 255 executions`。
- Drift / marking：`pretrade_weight_i = posttrade_weight_i_prev × (1+r_i)/(1+gross_return)`，cash return 为 0；unbalanced panel 对 close 做 past-only forward fill，missing observation 当日 return 为 0，下次真实 close 体现累计价格变化。
- Trade / cost：`gross_traded_weight=sum(abs(stock trade weights))`；turnover 是包含 cash leg 的 half-L1；transaction cost / slippage 按 gross stock traded weight 的 linear bps load 计算。
- Return accounting：`net_return=(1+gross_return)(1-total_cost)-1`，`nav(t)=nav(t-1)(1+net_return(t))`，`cumulative_pnl=nav-1`。
- Correctness review：next-global-date execution、no look-ahead、weight drift、scheduled rebalance、carry-forward target 不触发 daily rebalance、turnover / cost / NAV accounting、past-only marking 均已确认正确。

Production sanity（2021-01-04 ~ 2025-12-31）：

```text
position rows / symbols: 363,600 / 300
decision count / execution count: 256 / 255
gross traded weight (total/mean/max): 186.24369232 / 0.15366641 / 1.37753248
turnover (total/mean/max): 93.62184616 / 0.07724575 / 1.00000000
transaction cost load (sum): 0.09312185
slippage cost load (sum): 0.09312185
gross cumulative return: 102.06138410%
net cumulative return: 67.71308486%
ending NAV: 1.67713085
```

Cost load sums 是 daily cost rates 的简单求和，不是直接累计 NAV 损失。

- Verified tests：`uv run pytest tests/test_backtest.py tests/test_portfolio.py` → `10 passed in 0.73s`。
- Production runner：`uv run python scripts/run_backtest.py`。

## Day 6 — Analytics & Tests: DONE

- Core APIs：`annualized_return`、`annualized_volatility`、`sharpe_ratio`、`max_drawdown`、`summarize_performance`；production runner：`uv run python scripts/run_analytics.py`。
- Metric conventions：return 使用 daily `net_return` 复利，252 periods annualization；volatility 使用 sample std（`ddof=1`）；Sharpe 假设 risk-free rate 为 0，zero volatility 返回 `NaN`；drawdown 基于 NAV running peak 且结果不大于 0。
- NAV / turnover：daily summary 每行是一个完成的 return period，隐含初始 NAV 为 1.0；turnover 直接复用 Day 5 `turnover`，`annualized_turnover = average_daily_turnover * 252`。
- Production baseline（`uv run python scripts/run_analytics.py`）：annualized return `11.35049130%`、annualized volatility `24.30165667%`、Sharpe `0.56351490`、max drawdown `-35.63637308%`；total / average / annualized turnover `93.62184616 / 0.07724575 / 19.46592841`；ending NAV `1.67713085`、cumulative return `67.71308486%`。
- Tests：新增 deterministic compounded return、sample volatility / Sharpe、max drawdown、flat portfolio 和 Day 5 backtest integration sanity；受 Codex sandbox 限制未执行，需本地运行 `uv run pytest tests/test_backtest.py tests/test_analytics.py`。
- Day 5 contract review：未发现问题，也未修改 execution、return、cost 或 turnover semantics。

## Day 7 — End-to-End: DONE

- Baseline config：`configs/baseline.toml` 定义 processed data path、20 / 5 / 20 factor windows、1-step forward horizon、5 quantiles、`momentum_20d` Q5 portfolio、5 bps transaction cost、5 bps slippage 和 252 annualization periods。
- Pipeline API：`load_pipeline_config(path)` 和 `run_pipeline(config)`；一次加载 market data、一次计算三个 factors 和 forward return，随后串联 research、weekly long-only equal-weight portfolio、delayed-execution backtest 与 analytics。
- Structured result：返回 factor data、逐 factor IC / quantile results、factor correlation、target portfolio、positions、daily backtest 和 performance summary。
- One-command runner：`uv run python scripts/run_pipeline.py`，默认读取 baseline config；也支持显式 TOML path，并只打印紧凑 baseline summary。
- Integration tests：新增 baseline config sanity 与 deterministic E2E smoke test，覆盖完整 wiring、date ordering、metric keys、finite returns / NAV 和非空 executions；受 Codex sandbox 限制未执行。
- Correctness：未修改 Day 1–6 factor timing、forward return、quantile、portfolio、next-global-date execution、drift、turnover、cost、return / NAV 或 analytics semantics。
- Production baseline：本轮未在 Codex sandbox 运行 `uv`，因此不新增或推测 production 数字；沿用 Day 3 / 5 / 6 已记录的独立 production sanity results，待本地 one-command runner 验证。

## Known Limitations

- Frozen current-membership CSI300 universe 存在 survivorship / membership bias。
- Data provider 可能将当前 ticker identifier 回填到历史 observations。
- Unbalanced panel 的 factor rolling / research forward horizon 使用 available observations，而非 strict exchange-calendar sessions。
- Week 1 假设可以按 past-only marked close 理想化成交；不模拟 suspension 无法成交、limit up/down、bid/ask、volume participation、liquidity 或 market impact。

## Next — Day 8: Data Quality

补充 missing / duplicate / invalid data checks，并明确 adjustment 与 suspension handling rules。
