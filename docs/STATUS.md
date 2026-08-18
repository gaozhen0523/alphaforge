# Current Status

## Current Phase

Week 2 — Resume-Ready MVP

## Current Day

Day 10 — Out-of-Sample: DONE

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
- Baseline artifacts：runner 自动创建 `outputs/baseline/` 并覆盖写入 `factor_research.csv`、`daily_backtest.parquet` 和 `performance.json`；保存逻辑仅消费现有 `PipelineResult`，不重新计算指标。
- Correctness：未修改 Day 1–6 factor timing、forward return、quantile、portfolio、next-global-date execution、drift、turnover、cost、return / NAV 或 analytics semantics。
- Production baseline：本轮未在 Codex sandbox 运行 `uv`，因此不新增或推测 production 数字；沿用 Day 3 / 5 / 6 已记录的独立 production sanity results，待本地 one-command runner 验证。

## Day 8 — Data Quality: DONE

- Hard validation：扩展现有 `validate_ohlcv`，canonical observed row 明确拒绝 duplicate `(date, symbol)`、OHLCV NaN / non-finite、non-positive OHLC、negative volume，以及 high/low 与 open/close bounds violations；invalid data 不自动修复、drop 或补 row。
- Diagnostics API：新增 `summarize_ohlcv_quality(df)`，返回 rows、symbols、global dates、expected panel rows、observed unique rows、missing / coverage、duplicate pairs、invalid observations、internal missing 和 boundary missing。
- Missing semantics：expected panel 仅用于 diagnostics，Data Layer 继续保持 unbalanced observed panel；internal / boundary 只描述 gap location，不推断 suspension、IPO / delisting 或 provider gap 等真实原因。
- Adjustment / downstream semantics：production research 使用 `hfq` adjusted OHLC 规避 corporate-action mechanical jumps，但该 research series 不是历史 quoted execution price；factor / research 继续使用 available-observation semantics，Backtest 继续使用 past-only forward-filled close marking。Valuation fill 不代表 realistic tradability，Week 1 marked-close execution 仍是已知理想化假设。
- Production runner：新增 `uv run python scripts/run_data_quality.py`；本轮不记录或猜测 production diagnostics 数字。
- Tests：新增 deterministic tiny unbalanced panel coverage/internal/boundary calculation，并补充 explicit non-positive price / non-finite value validation；`uv` 在 Codex sandbox 中无法初始化 user cache，pytest 未进入 collection，尚未执行。

## Day 9 — Research Robustness: DONE

- Core APIs：新增 `compute_decay_return`、`compute_factor_decay_ic`、`summarize_yearly_ic` 和 `run_research_robustness`；multi-horizon research 继续复用 Day 3 的 `compute_forward_return`、daily IC / IC summary 和 quantile APIs。
- Multi-horizon：三个 baseline factors 固定分析 available-observation horizons `1 / 2 / 5 / 10`，逐 factor / horizon 汇总 valid IC days、mean IC、non-annualized ICIR 和 `mean(Q5 return) - mean(Q1 return)`；不选择 best horizon、不修改 factor definitions。
- Factor decay：`decay_return(t, lag=k) = close(t+k+1) / close(t+k) - 1`；offset 按各 symbol future available observations 计算并恢复到 formation row，IC 始终使用 `factor(t)`。`lag=0` 直接复用 horizon-1 forward return implementation，baseline lags 为 `0 / 1 / 2 / 3 / 4 / 5 / 10`。
- Yearly stability：复用 horizon-1 daily IC series，按 factor formation date 的 calendar year 汇总 factor、year、valid IC days、mean IC 和 ICIR，只作 descriptive analysis。
- Production runner：`uv run python scripts/run_research_robustness.py`；只加载 market data、计算三个 baseline factors 和 Day 9 research，不运行 portfolio / backtest。保存 `outputs/baseline/research_horizons.csv`、`factor_decay.csv` 和 `yearly_ic_stability.csv`。

Multi-horizon production results：

| Factor | Horizon | Valid IC days | Mean IC | ICIR | Q5−Q1 mean |
|---|---:|---:|---:|---:|---:|
| `momentum_20d` | 1 | 1,191 | -0.01432920 | -0.06249886 | 0.00029679 |
| `momentum_20d` | 2 | 1,190 | -0.01452612 | -0.06604244 | 0.00042596 |
| `momentum_20d` | 5 | 1,187 | -0.01542102 | -0.07283305 | 0.00062804 |
| `momentum_20d` | 10 | 1,182 | -0.01857031 | -0.08948986 | 0.00029403 |
| `reversal_5d` | 1 | 1,206 | 0.02155429 | 0.10352345 | -0.00020740 |
| `reversal_5d` | 2 | 1,205 | 0.01439332 | 0.07362202 | -0.00009052 |
| `reversal_5d` | 5 | 1,202 | 0.00727173 | 0.03823394 | -0.00012586 |
| `reversal_5d` | 10 | 1,197 | 0.00622264 | 0.03266437 | -0.00082532 |
| `volatility_20d` | 1 | 1,191 | -0.03175493 | -0.12444022 | 0.00080208 |
| `volatility_20d` | 2 | 1,190 | -0.03397301 | -0.13464029 | 0.00145014 |
| `volatility_20d` | 5 | 1,187 | -0.02778272 | -0.11091756 | 0.00339800 |
| `volatility_20d` | 10 | 1,182 | -0.02593504 | -0.10355749 | 0.00629665 |

Factor-decay mean IC：

| Factor | Lag 0 | Lag 1 | Lag 2 | Lag 3 | Lag 4 | Lag 5 | Lag 10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `momentum_20d` | -0.01432920 | -0.01033565 | -0.00923649 | -0.00853519 | -0.00825883 | -0.00481054 | -0.00833558 |
| `reversal_5d` | 0.02155429 | 0.01204611 | 0.00760575 | 0.00553533 | 0.00172225 | 0.00188520 | 0.00423668 |
| `volatility_20d` | -0.03175493 | -0.03279714 | -0.03210162 | -0.03127993 | -0.03027386 | -0.02987910 | -0.02947452 |

Yearly horizon-1 mean IC：

| Factor | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| `momentum_20d` | -0.01056921 | -0.01258497 | -0.01782710 | -0.00296899 | -0.02740053 |
| `reversal_5d` | 0.03010830 | 0.02465863 | 0.00322757 | 0.00455955 | 0.04535878 |
| `volatility_20d` | -0.01156337 | -0.03014409 | -0.04889107 | -0.05024698 | -0.01634385 |

- Production conclusion：`reversal_5d` exhibits clear short-horizon decay，mean IC 从 lag 0 的 `0.02155` 快速衰减，到 lag 4–5 接近 0；`volatility_20d` 的 negative rank association 在 lag 0–10 内较 persistent；`momentum_20d` 是 weak / noisy negative association，有 attenuation 但不是 clean monotonic decay。
- Yearly stability：三个 factor 的 horizon-1 mean IC 在 2021–2025 内 sign 均保持一致，但 magnitude 有明显 time variation。
- Interpretation：multi-horizon / decay / yearly analysis 仅作 descriptive robustness analysis，不用于选择 best horizon 或 tuning baseline。Longer-horizon forward returns overlap，daily IC observations 并非完全 independent；ICIR 不是严格 significance test；horizon / lag 均为 per-symbol available-observation offset，不是 strict exchange-calendar session offset。
- IC / quantile interpretation：Mean IC 衡量整个横截面的 Spearman rank relationship，Q5−Q1 只衡量 extreme quantiles 的 raw mean return spread；non-monotonic quantile profile 下两者 sign 可以不同，不据此修改 factor definitions。
- Quantile correctness fix：`summarize_quantile_returns()` 曾将 `top_minus_bottom` 计算为 mean of paired daily Q5−Q1 spreads，现已改为 exact contract `mean(Q5 return) - mean(Q1 return)`。当前 production dataset 上两种定义结果恰好一致；该修复不影响 IC、quantile assignment、portfolio selection、backtest、PnL 或其他 Day 1–8 semantics。
- Verified tests：`uv run pytest tests/test_quantiles.py tests/test_research_robustness.py` → `33 passed`；full suite `uv run pytest` → `176 passed, 2 expected ConstantInputWarning`。
- Production refresh：已重新运行 `run_factor_research.py`、`run_research_robustness.py` 和 `run_pipeline.py`，相关 baseline outputs 已按 exact quantile contract 刷新。

## Day 10 — Out-of-Sample: DONE

- 固定 chronological periods：IS = 2021–2023，OOS = 2024 / 2025；本轮只做 retrospective evaluation，不根据结果修改 factor、portfolio、execution、cost 或其他 frozen baseline definitions。
- Factor research：三个 baseline factors 先在完整 2021–2025 history 上按 past-only semantics 计算，再按 formation date 切 period；horizon-1 forward-return labels 在各 period 内独立计算，不跨 research boundary。逐 factor / period 汇总 valid IC days、mean IC、ICIR、Q1 / Q5 mean return 和 exact `mean(Q5) - mean(Q1)`。
- Strategy evaluation：完整 factors → weekly Q5 equal-weight portfolio → delayed-execution backtest 只连续运行一次；2023 decision 可以在 2024 下一 global date 合法执行，analytics boundary 不清仓、不 reset cash / position / strategy state。
- Period analytics：从 continuous daily backtest 按 period 切 `net_return` / turnover；return stream 在每个 period 内从 NAV 1 重新复利，仅用于 local cumulative return、ending NAV、risk 和 turnover summary，不改变底层 trading state。
- Core APIs：`assign_oos_period`、`compute_period_forward_return`、`run_out_of_sample_research`、`summarize_performance_by_period`；runner 为 `uv run python scripts/run_out_of_sample.py`，目标 outputs 为 `outputs/baseline/oos_factor_research.csv` 和 `oos_performance.csv`。
- Verified tests：`uv run pytest tests/test_out_of_sample.py tests/test_backtest.py tests/test_analytics.py tests/test_quantiles.py` → `46 passed in 2.13s`。Production runner 已成功生成 `outputs/baseline/oos_factor_research.csv` 和 `oos_performance.csv`。

Factor OOS production results：

| Factor | Period | Valid IC days | Mean IC | ICIR | Q5−Q1 |
|---|---|---:|---:|---:|---:|
| `momentum_20d` | IS 2021–2023 | 706 | -0.01404390 | -0.06200789 | 0.00002557 |
| `momentum_20d` | OOS 2024 | 241 | -0.00300710 | -0.01196298 | 0.00074496 |
| `momentum_20d` | OOS 2025 | 242 | -0.02740053 | -0.12763778 | 0.00062617 |
| `reversal_5d` | IS 2021–2023 | 721 | 0.01896301 | 0.09714561 | -0.00016418 |
| `reversal_5d` | OOS 2024 | 241 | 0.00486900 | 0.01962727 | -0.00066067 |
| `reversal_5d` | OOS 2025 | 242 | 0.04535878 | 0.22531863 | 0.00003242 |
| `volatility_20d` | IS 2021–2023 | 706 | -0.03011427 | -0.13570610 | 0.00066260 |
| `volatility_20d` | OOS 2024 | 241 | -0.04939381 | -0.16719233 | 0.00007833 |
| `volatility_20d` | OOS 2025 | 242 | -0.01634385 | -0.05475518 | 0.00208796 |

Frozen baseline strategy production results：

| Period | Annualized return | Volatility | Sharpe | Max drawdown | Cumulative return | Total turnover |
|---|---:|---:|---:|---:|---:|---:|
| IS 2021–2023 | -2.4579% | 22.5999% | 0.0028 | -35.6364% | -6.9278% | 55.8263 |
| OOS 2024 | 20.6151% | 27.9782% | 0.8072 | -16.4477% | 19.7213% | 19.6198 |
| OOS 2025 | 52.8102% | 25.2367% | 1.8079 | -15.7725% | 50.5135% | 18.1758 |

- Interpretation：factor IC / extreme-quantile spread 的 magnitude 明显 time-varying，且 IC 与 Q5−Q1 sign 不必一致；strategy OOS performance 高于 IS 仅作为 frozen-rule chronological evidence，不用于回头修改 baseline。
- Limitation：这些 OOS results 可能在 Day 12 的后续 factor combination research 中被再次查看，因此是 retrospective chronological robustness evidence，不是 permanently untouched final holdout。

## Known Limitations

- Frozen current-membership CSI300 universe 存在 survivorship / membership bias。
- Data provider 可能将当前 ticker identifier 回填到历史 observations。
- Unbalanced panel 的 factor rolling / research forward horizon 使用 available observations，而非 strict exchange-calendar sessions。
- Longer-horizon forward returns overlap；daily IC observations 不应解释为完全 independent，当前 ICIR 也不用于严格统计显著性判断。
- Week 1 假设可以按 past-only marked close 理想化成交；不模拟 suspension 无法成交、limit up/down、bid/ask、volume participation、liquidity 或 market impact。

## Next — Day 11: Cost Analysis

- transaction cost / slippage sensitivity
- analyze turnover impact without changing the frozen baseline
